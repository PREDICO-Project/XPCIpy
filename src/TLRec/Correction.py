import numpy as np

try:
    from numba import njit
except Exception as err:
    #print(f'Numba cannot be imported: {err}')
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

def calculate_C_matrix(images, xp=np):
    """Compute the covariance-like matrix C = images @ images.T.

    This is the single expensive step of the phase-step correction (one big matmul
    contracted over all pixels), so it is the part that benefits from running on GPU.
    Pass xp=cupy to run it on GPU; the resulting C then stays resident there.
    """
    if len(images.shape) == 3:
        (z,y,x) = images.shape
        images_2d = images.reshape(z, -1).astype(xp.float64, copy=False)
        C = images_2d @ images_2d.T
    else:
        z =images.shape[0]
        C = xp.zeros((z, z), dtype=xp.float64)
    C = xp.asarray(C)
    return C

@njit(parallel=True, cache=False) 
def GramSchmidt(A):
    (y,x) = A.shape
    U = np.zeros((y,x), dtype=np.float64)
    U[:,0] = A[:,0]/np.linalg.norm(A[:,0])
    
    for i in range(1,x):
        U[:,i] = A[:,i]
        for j in range(i):
            U[:,i] = U[:,i] - (np.dot(A[:,i], U[:,j]))/(np.dot(U[:,j],U[:,j]))*U[:,j]
        U[:,i] = U[:,i]/np.linalg.norm(U[:,i])
    return U.T

@njit(parallel=True, cache=False) 
def Improve_reconstruction_minimization_steps(errors, C):
    M = C.shape[0]
    A = np.ones((M, 3))
    steps = np.arange(0,M,1)*2*np.pi/M
    A[:,1] = np.cos(steps+errors)
    A[:,2] = np.sin(steps+errors)
    o = GramSchmidt(A)
    maximization = o[1].T@C@o[1] + o[2].T@C@o[2]
    return -maximization  
  
def Improve_reconstruction_minimization_dose_steps(variable, C):
    M = C.shape[0]
    errors = variable[0:M-1]
    dose_fluctuations = variable[-M+1:]
    
    A = np.ones((M, 3))
    steps = np.arange(0,M,1)*2*np.pi/M
    A[0,1] = np.cos(steps[0])
    A[0,2] = np.sin(steps[0])
    A[1:,1] = np.cos(steps[1:]+errors)
    A[1:,2] = np.sin(steps[1:]+errors)

    diag_elements = np.append([1], dose_fluctuations)
    D = np.diag(diag_elements)
    A = D@A
    o = GramSchmidt(A)
    maximization = o[0].T@C@o[0] + o[1].T@C@o[1] + o[2].T@C@o[2]
    return -maximization  


def GramSchmidt_xp(A, xp):
    """Backend-agnostic Gram-Schmidt used on GPU (the @njit GramSchmidt above is used on CPU).

    A is tiny (num_phase_steps x 3), so the plain Python loop here is negligible
    compared to the cost of the C matrix multiplications below.
    """
    (y,x) = A.shape
    U = xp.zeros((y,x), dtype=xp.float64)
    U[:,0] = A[:,0]/xp.linalg.norm(A[:,0])

    for i in range(1,x):
        U[:,i] = A[:,i]
        for j in range(i):
            U[:,i] = U[:,i] - (xp.dot(A[:,i], U[:,j]))/(xp.dot(U[:,j],U[:,j]))*U[:,j]
        U[:,i] = U[:,i]/xp.linalg.norm(U[:,i])
    return U.T


def Improve_reconstruction_minimization_steps_xp(errors, C, xp):
    """Backend-agnostic version of Improve_reconstruction_minimization_steps.

    Used when C already lives on GPU: only the small `errors` vector crosses the
    CPU/GPU boundary at each optimizer iteration, while the C matmuls stay on GPU.
    """
    M = C.shape[0]
    errors = xp.asarray(errors)
    A = xp.ones((M, 3), dtype=xp.float64)
    steps = xp.arange(0,M,1)*2*np.pi/M
    A[:,1] = xp.cos(steps+errors)
    A[:,2] = xp.sin(steps+errors)
    o = GramSchmidt_xp(A, xp)
    maximization = o[1].T@C@o[1] + o[2].T@C@o[2]
    return float(-maximization)