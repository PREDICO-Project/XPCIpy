import numpy as np
from pathlib import Path

class Source():
    
    def __init__(self, FWHM, Spectrum, energy, Beam_distribution, pixel_size):
        self.width = FWHM[0] # x-FWHM (microns)
        self.height = FWHM[1] # y-FWHM (microns)
        self.Spectrum = Spectrum 
        self.energy = energy
        self.mean_energy, self.energies, self.intensities = self.obtain_energies()
        self.Beam_distribution = Beam_distribution # Plane or Conical
        self.pixel_size = pixel_size
        

    def import_spectrum(self):
        """Enables to open and read the txt files inside 'Spectra' folder"""
        spectra_dir = Path(__file__).resolve().parents[2] / "Resources" / "Spectra"
        path = spectra_dir / f"{self.Spectrum}.txt"
        data = np.loadtxt(path, dtype=float, comments="#")
        if data.ndim != 2 or data.shape[1] < 2:
            raise ValueError(f"Spectrum file must have at least two columns: energy_keV intensity. Got shape {data.shape}")
        return data 
    
    def obtain_energies(self):
        """Return (mean_energy, energies, normalized_intensities)."""
        if self.Spectrum.lower() == "mono":
            energies = [self.energy]
            intensities = [1.0]
            mean_energy = self.energy
        else:
            spec = self.import_spectrum()
            energies = spec[:, 0]
            intensities = spec[:, 1]

            # Normalize to sum=1
            s = sum(intensities)
            intensities = intensities / s
            mean_energy = np.average(energies, weights=intensities)

        return mean_energy, energies, intensities

    def Source_PSF(self, H, W, current_pixel_size=None, Magnification=1.0):
        """
        Source PSF
        """
        # Just in case
        if Magnification <= 0:
            psf = np.zeros((H, W), float); psf[H//2, W//2] = 1.0
            return psf

        if current_pixel_size is None:
            current_pixel_size = self.pixel_size

        # Effective FWHM at the plane
        fwhm_x_eff_um = self.width * Magnification
        fwhm_y_eff_um = self.height * Magnification

        denom = 2.0 * np.sqrt(2.0 * np.log(2.0))
        sigma_x_px = (fwhm_x_eff_um / current_pixel_size) / denom
        sigma_y_px = (fwhm_y_eff_um / current_pixel_size) / denom

        yy = np.arange(H) - (H - 1) / 2.0
        xx = np.arange(W) - (W - 1) / 2.0
        X, Y = np.meshgrid(xx, yy, indexing="xy")

        # 2D Gaussian
        psf = np.exp(-0.5 * ((X / sigma_x_px) ** 2 + (Y / sigma_y_px) ** 2))

        ssum = psf.sum()
        if ssum > 0:
            psf /= ssum
        return psf
    
    def PSF_blurr(self, image, current_pixel_size=None, Magnification=1):
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
            psf = self.Source_PSF(H, W, current_pixel_size=current_pixel_size, Magnification=Magnification)
            #print(H,W)
            otf = np.fft.fft2(np.fft.ifftshift(psf)) # Optical Transfer Function
            img_ft = np.fft.fft2(image)
            blurred = np.fft.ifft2(img_ft * otf).real
            return blurred

        elif image.ndim == 3:
            Z, H, W = image.shape
            psf = self.Source_PSF(H, W, current_pixel_size=current_pixel_size,  Magnification=Magnification)
            otf = np.fft.fft2(np.fft.ifftshift(psf)) # Optical Transfer Function
            out = np.empty_like(image, dtype=float)
            for k in range(Z):
                img_ft = np.fft.fft2(image[k])
                out[k] = np.fft.ifft2(img_ft * otf).real
            return out

        else:
            raise ValueError("image must be 2D or 3D (Z,H,W).")  