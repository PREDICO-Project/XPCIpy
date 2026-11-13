import numpy as np
#from skimage.transform import resize, downscale_local_mean
from scipy.ndimage import zoom, gaussian_filter
from scipy.interpolate import interp1d

# TODO: Finish the detector response 
class Detector():
    def __init__(self, Image_option, pixel_size_detector, FWHM_detector, noise_type, pixel_size, gaussian_sigma=0.0, N0 = 1e5, QE =1.0, random_seed=None):
        self.Image_option = Image_option # "Ideal" or "Realistic"
        self.pixel_size_detector = float(pixel_size) if pixel_size_detector is None else float(pixel_size_detector) # microns, µm
        self.FWHM_detector = FWHM_detector # microns,µm
        self.noise_type = noise_type # "poisson", "gaussian", "poisson+gaussian", or None
        self.pixel_size = pixel_size #microns per pixel of the input grid
        self.gaussian_sigma = gaussian_sigma # Standard deviation for Gaussian noise
        self.N0 = N0 # Number of photons per pixel
        self.QE = QE # Future Quantum efficiency
        self.random_seed = random_seed
        self._rng = np.random.default_rng(random_seed)
        # Custom MTF (set via set_custom_MTF)
        self._custom_mtf_freq = None
        self._custom_mtf_values = None

    def set_custom_MTF(self, freq, mtf):
        """
        Store a user-measured 1D radial MTF to replace the analytical double-Gaussian PSF.

        When set, all blurring operations use this MTF instead of FWHM_detector.
        Use clear_custom_MTF() to revert to the analytical model.

        Parameters
        ----------
        freq : array-like
            Spatial frequencies in lp/mm. Must start at 0 and be monotonically increasing.
        mtf : array-like
            MTF values in [0, 1], same length as freq. MTF(0) should be ~1.

        Raises
        ------
        ValueError
            If arrays are inconsistent, freq[0] != 0, or mtf values are out of range.
        """
        freq = np.asarray(freq, dtype=float)
        mtf = np.asarray(mtf, dtype=float)
        if freq.shape != mtf.shape or freq.ndim != 1:
            raise ValueError("freq and mtf must be 1D arrays of the same length.")
        if freq.size < 2:
            raise ValueError("freq must have at least 2 points.")
        if not np.isclose(freq[0], 0.0):
            raise ValueError("freq must start at 0 (DC component).")
        if np.any(np.diff(freq) <= 0):
            raise ValueError("freq must be monotonically increasing.")
        if np.any(mtf < 0) or np.any(mtf > 1.0 + 1e-6):
            raise ValueError("mtf values must be in [0, 1].")
        self._custom_mtf_freq = freq
        self._custom_mtf_values = np.clip(mtf, 0.0, 1.0)

    def clear_custom_MTF(self):
        """Remove the custom MTF and revert to the analytical double-Gaussian PSF."""
        self._custom_mtf_freq = None
        self._custom_mtf_values = None

    def set_random_seed(self, random_seed=None):
        """Set or reset the detector RNG seed for reproducible noise."""
        self.random_seed = random_seed
        self._rng = np.random.default_rng(random_seed)

    def PSF(self, height, width, current_pixel_size=None):
        """
        Separable 2-Gaussian PSF. Returns a (height, width) kernel normalized to sum=1.

        Parameters
        ----------
        height, width : int
            PSF size (usually the image size for FFT convolution).
        current_pixel_size : float or None
            Pixel size (µm/px) of the image to be blurred. If None, uses self.pixel_size.
        """
        if current_pixel_size is None:
            current_pixel_size = self.pixel_size

        # If the user provided a measured MTF, build the PSF from it
        if self._custom_mtf_freq is not None:
            return self._psf_from_custom_mtf(height, width, current_pixel_size)

        # Convert FWHM to sigma 
        fwhm_px = self.FWHM_detector / current_pixel_size
        sigma_base = fwhm_px / (2.0 * np.sqrt(2.0 * np.log(2.0)))
        if sigma_base <= 0:
            psf = np.zeros((height, width), dtype=float)
            psf[height // 2, width // 2] = 1.0
            return psf
        sigma1 = sigma_base
        sigma2 = 3.0 * sigma_base
        w1, w2 = 0.90034, 0.099613

        # Centered coordinates in pixels
        yy = np.arange(height) - (height - 1) / 2.0
        xx = np.arange(width) - (width - 1) / 2.0
        X, Y = np.meshgrid(xx, yy, indexing="xy")

        def g(x, s):
            return np.exp(-0.5 * (x / s) ** 2)

        gx = w1 * g(X, sigma1) + w2 * g(X, sigma2) # Gaussian X-axis
        gy = w1 * g(Y, sigma1) + w2 * g(Y, sigma2) # Gaussian Y-axis
        psf = gx * gy

        psf_sum = psf.sum()
        if psf_sum > 0:
            psf /= psf_sum
        return psf

    def _psf_from_custom_mtf(self, height, width, current_pixel_size):
        """
        Build a 2D PSF kernel from the stored custom 1D radial MTF.

        The MTF is assumed to be radially symmetric. It is interpolated onto a 2D
        frequency grid and the PSF is recovered via IFFT.
        """
        pixel_size_mm = current_pixel_size / 1000.0

        # 2D frequency grid centred at (cy, cx) in lp/mm
        cy, cx = height // 2, width // 2
        fy = (np.arange(height) - cy) / (height * pixel_size_mm)
        fx = (np.arange(width) - cx) / (width * pixel_size_mm)
        FX, FY = np.meshgrid(fx, fy)
        r_2d = np.sqrt(FX ** 2 + FY ** 2)

        # Interpolate the 1D MTF onto the 2D radial grid
        # Beyond the measured range → 0 (no transfer)
        interp = interp1d(
            self._custom_mtf_freq,
            self._custom_mtf_values,
            kind="linear",
            bounds_error=False,
            fill_value=(self._custom_mtf_values[0], 0.0),
        )
        mtf_2d = interp(r_2d)

        # Assume real, symmetric OTF (zero phase): OTF = MTF
        # IFFT to recover PSF; ifftshift to place DC at [0,0] for numpy's convention
        otf_centred = np.fft.ifftshift(mtf_2d)
        psf = np.fft.ifft2(otf_centred).real
        psf = np.fft.fftshift(psf)

        # Clip numerical negatives and normalise to sum = 1
        psf = np.clip(psf, 0.0, None)
        psf_sum = psf.sum()
        if psf_sum > 0:
            psf /= psf_sum
        return psf

    def PSF_blurr(self, image, current_pixel_size=None):
        """
        Blur an image or a stack with the detector PSF via FFT convolution.

        Parameters
        ----------
        image : np.ndarray
            2D (H, W) or 3D (Z, H, W).
        current_pixel_size : float or None
            Pixel size (µm) of 'image'. If None, uses self.pixel_size.

        Returns
        -------
        np.ndarray
            Blurred image with the same shape as input.
        """

        if current_pixel_size is None:
            current_pixel_size = self.pixel_size

        if image.ndim == 2:
            H, W = image.shape
            psf = self.PSF(H, W, current_pixel_size=current_pixel_size)
            otf = np.fft.fft2(np.fft.ifftshift(psf)) # Optical Transfer Function
            img_ft = np.fft.fft2(image)
            blurred = np.fft.ifft2(img_ft * otf).real
            return blurred

        elif image.ndim == 3:
            Z, H, W = image.shape
            psf = self.PSF(H, W, current_pixel_size=current_pixel_size)
            otf = np.fft.fft2(np.fft.ifftshift(psf)) # Optical Transfer Function
            out = np.empty_like(image, dtype=float)
            for k in range(Z):
                img_ft = np.fft.fft2(image[k])
                out[k] = np.fft.ifft2(img_ft * otf).real
            return out

        else:
            raise ValueError("image must be 2D or 3D (Z,H,W).")      
          
    def add_noise(self, image):
        """
        Add Gaussian, Poisson, or combined Poisson+Gaussian noise.

        Parameters
        ----------
        image : np.ndarray (2D)
        """
        if self.noise_type is None:
            return image

        noise = self.noise_type.lower()

        valid_modes = ("poisson", "gaussian", "poisson+gaussian", "gaussian+poisson")
        if noise not in valid_modes:
            raise ValueError("Unknown noise_type. Use 'gaussian', 'poisson', 'poisson+gaussian', or None.")

        use_poisson = "poisson" in noise
        use_gaussian = "gaussian" in noise

        out = image

        if use_poisson:
            if self.N0 <= 0:
                raise ValueError("N0 must be greater than 0 for Poisson noise.")
            if self.QE <= 0:
                raise ValueError("QE must be greater than 0 for Poisson noise.")
            counts = out * self.N0 * self.QE
            counts = self._rng.poisson(np.clip(counts, 0, None))
            out = counts / (self.N0 * self.QE)

        # Gaussian noise
        if use_gaussian:
            if self.gaussian_sigma > 0:
                out = out + self._rng.normal(0.0, self.gaussian_sigma, size=out.shape)

        return out

    def downsample_image(self, image, current_pixel_size=None):
        """
        Downsample 'image' to the detector pitch using local mean for integer factors,
        otherwise use linear resize with anti-aliasing.

        Parameters
        ----------
        image : np.ndarray
            2D (H, W) or 3D (Z, H, W).
        current_pixel_size : float or None
            Pixel size (µm/px) of 'image'. If None, uses self.pixel_size.
        """
        if current_pixel_size is None:
            current_pixel_size = self.pixel_size

        if current_pixel_size <= 0:
            raise ValueError("current_pixel_size must be > 0.")

        
        factor = self.pixel_size_detector / float(current_pixel_size)

        if factor <= 0:
            raise ValueError("pixel_size_detector must be > 0.")
        
        if np.isclose(factor, 1.0):
            return image.copy()

        if image.ndim == 3:
            return np.stack(
                [
                    self.downsample_image(image[k], current_pixel_size=current_pixel_size)
                    for k in range(image.shape[0])
                ],
                axis=0,
            )

        if image.ndim != 2:
            raise ValueError("image must be 2D or 3D (Z,H,W).")

        
        int_factor = int(round(factor))
        if np.isclose(factor, int_factor, atol=1e-6):
            #print("downsample local mean")
            H, W = image.shape
            if int_factor > min(H, W):
                new_shape = (max(1, int(round(H / factor))), max(1, int(round(W / factor))))
                return self._resize_linear_reflect(image, new_shape)
            Hc = (H // int_factor) * int_factor
            Wc = (W // int_factor) * int_factor
            cropped = image[:Hc, :Wc]
            #return downscale_local_mean(cropped, (int_factor, int_factor))
            return self._downscale_local_mean_numpy(cropped, int_factor)
        # Slower
        else:
            new_shape = (max(1, int(round(image.shape[0] / factor))), max(1, int(round(image.shape[1] / factor))),)
            #return resize(image, new_shape, order=1, mode="reflect", anti_aliasing=True, preserve_range=True)
            return self._resize_linear_reflect(image, new_shape)

    def applyDetector(self, image, current_pixel_size=None):
        """
        Apply detector
        """
        if current_pixel_size is None:
            current_pixel_size = self.pixel_size

        if self.Image_option == "Ideal":
            out = self.downsample_image(image, current_pixel_size=current_pixel_size) # There was a bug here
            return out

        # Realistic
        blurred = self.PSF_blurr(image, current_pixel_size=current_pixel_size)
        down = self.downsample_image(blurred, current_pixel_size=current_pixel_size)
        

        if self.noise_type is None:
            return down
        return self.add_noise(down)


    def _resize_linear_reflect(self, image, new_shape):
        new_h, new_w = new_shape
        scale_h = new_h / image.shape[0]
        scale_w = new_w / image.shape[1]
        out = image.astype(float)

        # Anti-aliasing approximation
        if scale_h < 1 or scale_w < 1:
            sigma_h = max(0, (1/scale_h - 1) * 0.5)
            sigma_w = max(0, (1/scale_w - 1) * 0.5)
            out = gaussian_filter(out, sigma=(sigma_h, sigma_w), mode="reflect")

        zoom_factors = (scale_h, scale_w)
        return zoom(out, zoom_factors, order=1, mode="reflect")
    
    def compute_MTF(self, pixel_size=None, n_pts=512):
        """
        Compute the radially averaged Modulation Transfer Function (MTF) from the detector PSF.

        Parameters
        ----------
        pixel_size : float or None
            Pixel size in µm/px. If None, uses self.pixel_size.
        n_pts : int
            Grid size used to evaluate the PSF/MTF.

        Returns
        -------
        freq : np.ndarray
            Spatial frequencies in lp/mm.
        mtf : np.ndarray
            1D radially-averaged MTF, normalized so that MTF(0) = 1.
        """
        if pixel_size is None:
            pixel_size = self.pixel_size
        if pixel_size <= 0:
            raise ValueError("pixel_size must be > 0.")

        psf = self.PSF(n_pts, n_pts, current_pixel_size=pixel_size)

        otf = np.fft.fft2(np.fft.ifftshift(psf))
        mtf_2d = np.abs(np.fft.fftshift(otf))

        dc = mtf_2d[n_pts // 2, n_pts // 2]
        if dc > 0:
            mtf_2d /= dc

        pixel_size_mm = pixel_size / 1000.0
        df = 1.0 / (n_pts * pixel_size_mm)

        cy, cx = n_pts // 2, n_pts // 2
        y_idx, x_idx = np.mgrid[0:n_pts, 0:n_pts]
        r_px = np.sqrt((x_idx - cx) ** 2 + (y_idx - cy) ** 2)

        r_max = n_pts // 2
        r_bins = np.arange(0, r_max + 1)
        mtf_1d = np.zeros(len(r_bins))
        for i, r in enumerate(r_bins):
            mask = (r_px >= r - 0.5) & (r_px < r + 0.5)
            if mask.any():
                mtf_1d[i] = mtf_2d[mask].mean()

        freq = r_bins * df  # lp/mm
        return freq, mtf_1d

    def compute_NPS(self, n_images=50, image_shape=(256, 256), pixel_size=None):
        """
        1D radially averaged Noise Power Spectrum (NPS) from simulated flat-field noisy images.

        Parameters
        ----------
        n_images : int
        image_shape : tuple of int
            (H, W) of each flat-field image
        pixel_size : float or None
            Pixel size in micrometers/px. If None, uses self.pixel_size.

        Returns
        -------
        freq : np.ndarray
            Spatial frequencies in lp/mm.
        nps : np.ndarray
            1D radially-averaged NPS in mm^2  (noise variance per spatial-frequency
            bin, normalised by detector pixel area and number of pixels).

        Raises
        ------
        ValueError
            If noise_type is None (NPS is zero for a noiseless detector).
        """
        if self.noise_type is None:
            raise ValueError(
                "noise_type is None; NPS is identically zero for a noiseless detector."
            )
        if n_images < 1:
            raise ValueError("n_images must be >= 1.")
        if pixel_size is None:
            pixel_size = self.pixel_size
        if pixel_size <= 0:
            raise ValueError("pixel_size must be > 0.")

        H, W = image_shape
        pixel_size_mm = pixel_size / 1000.0
        flat = np.ones((H, W), dtype=float)

        nps_sum = np.zeros((H, W), dtype=float)
        for _ in range(n_images):
            noisy = self.add_noise(flat.copy())
            detrended = noisy - noisy.mean()
            nps_sum += np.abs(np.fft.fftshift(np.fft.fft2(detrended))) ** 2

        nps_2d = (pixel_size_mm ** 2 / (H * W)) * (nps_sum / n_images)

        cy, cx = H // 2, W // 2
        y_idx, x_idx = np.mgrid[0:H, 0:W]
        df_h = 1.0 / (H * pixel_size_mm)
        df_w = 1.0 / (W * pixel_size_mm)
        fy = (y_idx - cy) * df_h
        fx = (x_idx - cx) * df_w
        r = np.sqrt(fx ** 2 + fy ** 2)

        df = min(df_h, df_w)
        r_max = min(cy * df_h, cx * df_w)
        r_bins = np.arange(0, r_max, df)

        nps_1d = np.zeros(len(r_bins))
        for i, r_center in enumerate(r_bins):
            mask = (r >= r_center - df / 2) & (r < r_center + df / 2)
            if mask.any():
                nps_1d[i] = nps_2d[mask].mean()

        return r_bins, nps_1d

    def _downscale_local_mean_numpy(self, image, int_factor):
        """
        Similar to skimage.transform.downscale_local_mean
        """
        H, W = image.shape
        Hc = (H // int_factor) * int_factor
        Wc = (W // int_factor) * int_factor
        cropped = image[:Hc, :Wc]
       
        return cropped.reshape(Hc // int_factor, int_factor, Wc // int_factor, int_factor).mean(axis=(1, 3))

