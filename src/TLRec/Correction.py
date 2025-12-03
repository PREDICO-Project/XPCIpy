import numpy as np

try:
    from numba import njit
except Exception as err:
    #print(f'Numba cannot be imported: {err}')
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

def calculate_C_matrix(images):
    if len(images.shape) == 3:
        (z,y,x) = images.shape
        
    else:
        z =images.shape[0]
        x = 0
        y = 0
    C = np.zeros((z,z), dtype=np.float64)
    i = 0
    for ii in range(0,x,1):
        for jj in range(0,y,1):
            I = np.reshape(images[:,jj,ii], (z,1))
            I_T = np.transpose(I)           
            C_xy = np.matmul(I,I_T, dtype=np.float64)
            i +=1
            C += C_xy      
    C = np.asarray(C)   
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