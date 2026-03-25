import numpy as np
#from skimage.transform import resize, downscale_local_mean
from scipy.ndimage import zoom, gaussian_filter

# TODO: Finish the detector response 
class Detector():
    def __init__(self, Image_option, pixel_size_detector, FWHM_detector, noise_type, pixel_size, gaussian_sigma=0.0, N0 = 1e5, QE =1.0):
        self.Image_option = Image_option # "Ideal" or "Realistic"
        self.pixel_size_detector = float(pixel_size) if pixel_size_detector is None else float(pixel_size_detector) # microns, µm
        self.FWHM_detector = FWHM_detector # microns,µm
        self.noise_type = noise_type # "poisson", "gaussian", or None
        self.pixel_size = pixel_size #microns per pixel of the input grid
        self.gaussian_sigma = gaussian_sigma # Standard deviation for Gaussian noise
        self.N0 = N0 # Number of photons per pixel
        self.QE = QE # Future Quantum efficiency

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

        # Convert FWHM to sigma 
        fwhm_px = self.FWHM_detector / current_pixel_size
        sigma_base = fwhm_px / (2.0 * np.sqrt(2.0 * np.log(2.0)))
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
        Add simple Gaussian or Poisson noise.

        Parameters
        ----------
        image : np.ndarray (2D)
        """
        if self.noise_type is None:
            return image
        
        if self.noise_type.lower() == "poisson":
            if self.N0 > 0:
                counts = image * self.N0
                
                counts = counts * self.QE
                
                rng = np.random.default_rng()
                counts = rng.poisson(np.clip(counts, 0, None))

                out = counts / (self.N0 * self.QE)
                return out
        
        # Gaussian noise
        if self.noise_type.lower() == "gaussian":
            if self.gaussian_sigma <= 0:
                return image
            rng = np.random.default_rng()
            return image + rng.normal(0.0, self.gaussian_sigma, size=image.shape)
            
        else:
            raise ValueError("Unknown noise_type. Use 'gaussian', 'poisson', or None.")

    def downsample_image(self, image, current_pixel_size=None):
        """
        Downsample 'image' to the detector pitch using local mean for integer factors,
        otherwise use linear resize with anti-aliasing.

        Parameters
        ----------
        image : np.ndarray (2D)
        current_pixel_size : float or None
            Pixel size (µm/px) of 'image'. If None, uses self.pixel_size.
        """
        if current_pixel_size is None:
            current_pixel_size = self.pixel_size

        
        factor = self.pixel_size_detector / float(current_pixel_size)
        
        if np.isclose(factor, 1.0):
            return image.copy()

        
        int_factor = int(round(factor))
        if np.isclose(factor, int_factor, atol=1e-6):
            #print("downsample local mean")
            H, W = image.shape
            Hc = (H // int_factor) * int_factor
            Wc = (W // int_factor) * int_factor
            cropped = image[:Hc, :Wc]
            #return downscale_local_mean(cropped, (int_factor, int_factor))
            return self._downscale_local_mean_numpy(cropped, int_factor)
        # Slower
        else:
            new_shape = (int(round(image.shape[0] / factor)),
                            int(round(image.shape[1] / factor)))
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
    
    def _downscale_local_mean_numpy(self, image, int_factor):
        """
        Similar to skimage.transform.downscale_local_mean
        """
        H, W = image.shape
        Hc = (H // int_factor) * int_factor
        Wc = (W // int_factor) * int_factor
        cropped = image[:Hc, :Wc]
       
        return cropped.reshape(Hc // int_factor, int_factor, Wc // int_factor, int_factor).mean(axis=(1, 3))

