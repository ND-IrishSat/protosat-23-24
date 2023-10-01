'''
UKF_algorithm.py
Authors: Andrew Gaylord, Claudia Kuczun, Micheal Paulucci, Alex Casillas, Anna Arnett
Last modified 9/26/23

UKF algorithm for IrishSat based on following resource:
https://towardsdatascience.com/the-unscented-kalman-filter-anything-ekf-can-do-i-can-do-it-better-ce7c773cf88d

Variables needed throughout UKF process:
  n = dimensionality of model (10)
  m = dimension of measurement space that excludes first 0 of quaternion (9)
  r = noise vector for predictions (we choose this & make it) (n)
  q = noise vector for sensors (provided on data sheet for sensors) (m)
  scaling = parameter for sigma point generation (3 - n)
  cov = initial covariance matrix (n x n)
  predMeans = matrix of predicted means (1 x n)
  predCovid = matrix of predicted covariance (n x n)
  g = matrix of predicted sigma points (state space using EOMs) (2*n+1 x n)
  h = matrix of transformed sigma points (in the measurement space) (2*n+1 x m)
  q_wmm = B field represented as quaternion (1 x 4)
  meanInMes = means in the measurement space (1 x m)
  covidInMes = covariance matrix of points in measurement space (m x m)
  z = sensor data (1 x n except switched to 1 x m for some calculations)
  kalman = kalman gain for each step (n x m)
'''

import numpy as np
import math
from bigEOMS import *
import random
import scipy
import scipy.linalg
#from statsmodels import *
#from statsmodels.stats import correlation_tools

"""
Calculate sigma points
Use mean and covariance matrices to make sigma point matrix
"""

def sigma(means, cov, n, scaling):
    #temp=np.zeros((len(cov,n)))

  
    '''hardcode 10 here'''
    sigmaMatrix = np.zeros((2*n+1,n))
    temp = np.zeros((n, n))

    # intialize 2N + 1 sigma points to zeroes

    #print("MATRIX INSIDE SIGMA: ", sigmaMatrix)
    #set first row to means here?
    for i in range(len(cov)):
      for j in range(len(cov[i])):
        #from website formula
        temp[i][j] = cov[i][j]  * (n + scaling)
    # temp=cov*(n+scaling)
    # temp = cov
    # print(temp)

    # print("TEMP BEFORE", temp)

    # print("E VALUES: ", np.linalg.eigvalsh(temp))
    # P, L, U = scipy.linalg.lu(temp)

    # temp = correlation_tools.cov_nearest(temp)
    # temp = np.transpose(scipy.linalg.cholesky(temp,lower=True))
    # temp = scipy.linalg.cholesky(temp,lower=True)
    # print(len(temp), "   ", len(temp[0]))
    temp = scipy.linalg.sqrtm(temp)
    sigmaMatrix[0] = means

    # print("TEMP AFTER ", temp)
    
    # traverse N (10) dimensions, calculating all sigma points
    for i in range(n):
        sigmaMatrix[i + 1] = np.add(means, temp[i])  # mean + covariance
        sigmaMatrix[i + 1 + n] = np.subtract(means, temp[i])  # mean - covariance

    # return the sigma matrix (21 columns)
    # print("CALING FUNC", sigmaMatrix)
    return sigmaMatrix


"""
Equations of motion
Using the current state of the system, output the new predicted state of the system 
Use the new collected means & covariance to make next sigma point matrix using the Equations of Motion
"""

def EOMs(state):
    ''' Transformation function x_k_plus = f(x_k, u_k)
    
        Args:
            state: State of the system vector
                [a b c d w_x w_y w_z theta_dot_RW1 theta_dot_RW2 theta_dot_RW3]
              
            u_k: Control input vector (Currently, magnetorquers are not being used, all set to 0)
                [t_motor1, t_motor2, t_motor3, M_mt1, M_mt2, M_mt3]
                
            I_body_tensor: Moment of inertia tensor of the cubesat
                [[I_XX  I_XY  I_XZ]
                 [I_YX  I_YY  I_YZ]
                 [I_ZX  I_ZY  I_ZZ]]
            
            I_RW: Moment of inertias of the three reaction wheels
                [I_RW1 I_RW2 I_RW3]
                
            dt: The timestep between the current state and predicted state
            
            func: instance of EoMs object, defined in eoms.py
    '''
    func = bigEOMS()

    u_k = np.zeros(6)
    I_body_tensor = [[1728.7579, -60.6901, -8.7583],
                     [-60.6901, 1745.997, 53.4338],
                     [-8.7583, 53.4338, 1858.2584]]
    I_RW = [578.5944, 578.5944, 578.5944]
    dt = 0.1

    # Initialize prediction
    x_predicted = np.zeros(len(state))

    ## Grab intermediate values
    # Grab components of state vector
    a = state[0]
    b = state[1]
    c = state[2]
    d = state[3]
    w_x = state[4]
    w_y = state[5]
    w_z = state[6]
    theta_dot_RW1 = state[7]
    theta_dot_RW2 = state[8]
    theta_dot_RW3 = state[9]

    # Grab moment of inertias
    I_xx = I_body_tensor[0][0]
    I_xy = I_body_tensor[0][1]
    I_xz = I_body_tensor[0][2]
    I_yx = I_body_tensor[1][0]
    I_yy = I_body_tensor[1][1]
    I_yz = I_body_tensor[1][2]
    I_zx = I_body_tensor[2][0]
    I_zy = I_body_tensor[2][1]
    I_zz = I_body_tensor[2][2]
    I_RW1_XX = I_RW[0]
    I_RW2_YY = I_RW[1]
    I_RW3_ZZ = I_RW[2]

    # Grab components of control input
    t_motor1 = u_k[0]
    t_motor2 = u_k[1]
    t_motor3 = u_k[2]
    M_mt1 = u_k[3]
    M_mt2 = u_k[4]
    M_mt3 = u_k[5]

    # Do Euler's method to get next state
    x_predicted[0] = state[0] + dt * func.adot(a, b, c, d, w_x, w_y, w_z)
    x_predicted[1] = state[1] + dt * func.bdot(a, b, c, d, w_x, w_y, w_z)
    x_predicted[2] = state[2] + dt * func.cdot(a, b, c, d, w_x, w_y, w_z)
    x_predicted[3] = state[3] + dt * func.ddot(a, b, c, d, w_x, w_y, w_z)
    x_predicted[4] = state[4] + dt * func.w_dot_x(
        M_mt1, M_mt2, M_mt3, t_motor1, t_motor2, t_motor3, w_x, w_y, w_z, I_xx,
        I_xy, I_xz, I_yx, I_yy, I_yz, I_zx, I_zy, I_zz, I_RW1_XX, I_RW2_YY,
        I_RW3_ZZ, theta_dot_RW1, theta_dot_RW2, theta_dot_RW3)
    x_predicted[5] = state[5] + dt * func.w_dot_y(
        M_mt1, M_mt2, M_mt3, t_motor1, t_motor2, t_motor3, w_x, w_y, w_z, I_xx,
        I_xy, I_xz, I_yx, I_yy, I_yz, I_zx, I_zy, I_zz, I_RW1_XX, I_RW2_YY,
        I_RW3_ZZ, theta_dot_RW1, theta_dot_RW2, theta_dot_RW3)
    x_predicted[6] = state[6] + dt * func.w_dot_z(
        M_mt1, M_mt2, M_mt3, t_motor1, t_motor2, t_motor3, w_x, w_y, w_z, I_xx,
        I_xy, I_xz, I_yx, I_yy, I_yz, I_zx, I_zy, I_zz, I_RW1_XX, I_RW2_YY,
        I_RW3_ZZ, theta_dot_RW1, theta_dot_RW2, theta_dot_RW3)
    x_predicted[7] = state[7] + dt * func.theta_ddot_RW1(
        M_mt1, M_mt2, M_mt3, t_motor1, t_motor2, t_motor3, w_x, w_y, w_z, I_xx,
        I_xy, I_xz, I_yx, I_yy, I_yz, I_zx, I_zy, I_zz, I_RW1_XX, I_RW2_YY,
        I_RW3_ZZ, theta_dot_RW1, theta_dot_RW2, theta_dot_RW3)
    x_predicted[8] = state[8] + dt * func.theta_ddot_RW2(
        M_mt1, M_mt2, M_mt3, t_motor1, t_motor2, t_motor3, w_x, w_y, w_z, I_xx,
        I_xy, I_xz, I_yx, I_yy, I_yz, I_zx, I_zy, I_zz, I_RW1_XX, I_RW2_YY,
        I_RW3_ZZ, theta_dot_RW1, theta_dot_RW2, theta_dot_RW3)
    x_predicted[9] = state[9] + dt * func.theta_ddot_RW3(
        M_mt1, M_mt2, M_mt3, t_motor1, t_motor2, t_motor3, w_x, w_y, w_z, I_xx,
        I_xy, I_xz, I_yx, I_yy, I_yz, I_zx, I_zy, I_zz, I_RW1_XX, I_RW2_YY,
        I_RW3_ZZ, theta_dot_RW1, theta_dot_RW2, theta_dot_RW3)

    return x_predicted


"""
H function: update function (predict measurement from predicted state)
  transform sigma points to measurement space. Only quaternian needs to change. 
  state space -> measurement space


Functions of getting predicted measurement from magnetometer (quaternion of B-field in body frame) from state (quaternion of body frame with reference to ECI)
"""


def observe_a_B_BF(a_kf, b_kf, c_kf, d_kf, a_wmm, b_wmm, c_wmm, d_wmm):
    return b_kf*(a_kf*b_wmm - c_kf*d_wmm + c_wmm*d_kf) - a_kf*(b_kf*b_wmm + c_kf*c_wmm + d_kf*d_wmm) + c_kf*(a_kf*c_wmm + b_kf*d_wmm - b_wmm*d_kf) + d_kf*(a_kf*d_wmm - b_kf*c_wmm + b_wmm*c_kf)


def observe_b_B_BF(a_kf, b_kf, c_kf, d_kf, a_wmm, b_wmm, c_wmm, d_wmm):
    return a_kf*(a_kf*b_wmm - c_kf*d_wmm + c_wmm*d_kf) - c_kf*(a_kf*d_wmm - b_kf*c_wmm + b_wmm*c_kf) + b_kf*(b_kf*b_wmm + c_kf*c_wmm + d_kf*d_wmm) + d_kf*(a_kf*c_wmm + b_kf*d_wmm - b_wmm*d_kf)


def observe_c_B_BF(a_kf, b_kf, c_kf, d_kf, a_wmm, b_wmm, c_wmm, d_wmm):
    return a_kf*(a_kf*c_wmm + b_kf*d_wmm - b_wmm*d_kf) + b_kf*(a_kf*d_wmm - b_kf*c_wmm + b_wmm*c_kf) + c_kf*(b_kf*b_wmm + c_kf*c_wmm + d_kf*d_wmm) - d_kf*(a_kf*b_wmm - c_kf*d_wmm + c_wmm*d_kf)


def observe_d_B_BF(a_kf, b_kf, c_kf, d_kf, a_wmm, b_wmm, c_wmm, d_wmm):
    return a_kf*(a_kf*d_wmm - b_kf*c_wmm + b_wmm*c_kf) - b_kf*(a_kf*c_wmm + b_kf*d_wmm - b_wmm*d_kf) + c_kf*(a_kf*b_wmm - c_kf*d_wmm + c_wmm*d_kf) + d_kf*(b_kf*b_wmm + c_kf*c_wmm + d_kf*d_wmm)


# Observation function: z = h(x_k, u_k)
# might add a gps aspect to better calculate body frame
def H_func(state, q_wmm):  #magnetic field to quaternion RE-ADD q_wmm
    ''' Observation function:
    
        Args:
            q_wmm: quaternion of B_field w/ respect to the ECI frame. FIRST VALUE SHOULD BE 0
            state: state x_k of system
            
                              a_kf
                              b_kf
                              c_kf
                              d_kf
                              w_x
                     x_kf =   w_y
                              w_z
                              theta_dot_RW1
                              theta_dot_RW2
                              theta_dot_RW3

           
        The observation function maps that measurement z_kf from state x_kf such that
        z_kf = h(x_kf), where z_kf in this case is the following vector
        
                              a_B^BF      
                              b_B^BF
                              c_B^BF
                              d_B^BF
                    z_kf =    w_x
                              w_y
                              w_z
                              theta_dot_RW1
                              theta_dot_RW2
                              theta_dot_RW3
    
    '''

    # Grab components from vectors
    a_kf = state[0]
    b_kf = state[1]
    c_kf = state[2]
    d_kf = state[3]
    w_x = state[4]
    w_y = state[5]
    w_z = state[6]
    theta_dot_RW1 = state[7]
    theta_dot_RW2 = state[8]
    theta_dot_RW3 = state[9]

    a_wmm = q_wmm[0]
    b_wmm = q_wmm[1]
    c_wmm = q_wmm[2]
    d_wmm = q_wmm[3]
    #print(a_kf, b_kf, c_kf, d_kf, b_wmm, c_wmm, d_wmm)
    # Perform observation function, only needed for quaternion components. The rest have 1 to 1 mapping
    a_B_BF = 0  # For now, assume this will always be zero. Trust P. Wensing?
    '''CHANGED'''
    # a_B_BF = observe_a_B_BF(a_kf, b_kf, c_kf, d_kf, a_wmm, b_wmm, c_wmm, d_wmm)
    b_B_BF = observe_b_B_BF(a_kf, b_kf, c_kf, d_kf, a_wmm, b_wmm, c_wmm, d_wmm)
    c_B_BF = observe_c_B_BF(a_kf, b_kf, c_kf, d_kf, a_wmm, b_wmm, c_wmm, d_wmm)
    d_B_BF = observe_d_B_BF(a_kf, b_kf, c_kf, d_kf, a_wmm, b_wmm, c_wmm, d_wmm)

    # Observation vector
    za = np.array([
        b_B_BF, c_B_BF, d_B_BF, w_x, w_y, w_z, theta_dot_RW1,
        theta_dot_RW2, theta_dot_RW3
    ])

    
    #normalized version if we need it idk
    #should already be normal, but isn't occasually due to rounding errors. Could normalize sometimes
    '''
    normalize=1/math.sqrt(abs(a_B_BF*a_B_BF + b_B_BF*b_B_BF + c_B_BF*c_B_BF + d_B_BF*d_B_BF))
    Nza = np.array([
        a_B_BF * normalize, b_B_BF * normalize, c_B_BF * normalize, 
        d_B_BF * normalize, w_x, w_y, w_z, theta_dot_RW1,
        theta_dot_RW2, theta_dot_RW3
    ])
    '''
    
    return za


"""
Get the means in the measurement space (used in cross-covariance and final mean calculation)
  Using sigma points, p
  ???? what is this
"""
# get new info from sensors

#def getQvmm ():
"""
  This is stuff that Claudia is writing that we are getting from the magnetorquers
  Going to normalize aswell (divide by magnitude of bx by and bz)
  """
# q_wmm is supposed to be B field represented as quaternion. Bx / magnatude(B)


  #return [0, bx, by, bz]



# custom function to perform quaternion multiply on two passed-in matrices
def quaternionMultiply(a, b):
    return [[a[0] * b[0] - a[1] * b[1] - a[2] * b[2] - a[3] * b[3]],
            [a[0] * b[1] + a[1] * b[0] + a[2] * b[3] - a[3] * b[2]],
            [a[0] * b[2] - a[1] * b[3] + a[2] * b[0] + a[3] * b[1]],
            [a[0] * b[3] + a[1] * b[2] - a[2] * b[1] + a[3] * b[0]]]

# add state parameter??
def UKF(passedMeans, passedCov, r, q, data):

    # f = open("data_temp.txt", "r")
    # full = f.read()
    # split = full.split(")")
    # split = split[:-1]
    # split2 = []
    # for thing in split:
    #     temp = thing.split(",")
    #     # if(len(temp)<3):
    #     #     continue
    #     for t in range(0, len(temp)): 
    #         temp[t] = float(temp[t][1:])
        
    #     split2.append(temp)
    # # split2 = split.split(",")
    # # print(split2)
    # gyro = []
    # mag = []
    # for i in range(len(split2)):
    #     if(i%2==0):
    #         gyro.append(split2[i])
    #     else:
    #         mag.append(split2[i])
    # print(len(gyro))
    # print(len(mag))



    n = 10
    m = 9
    cov = passedCov
    #cov = []
    predCovid = np.zeros((n,n))
    meanInMes = np.zeros(m)
    covidInMes = np.zeros(m)
    h = np.zeros((2*n+1,m))
    g = np.zeros((n * 2 + 1, n))
    # q_wmm = [0, 5, 5, 5]
    q_wmm = []
    q_wmm.append(0)
    q_wmm.append(data[0])
    q_wmm.append(data[1])
    q_wmm.append(data[2])
    # z = passedMeans
    z=[]
    z.append(0)
    z.append(data[0])
    z.append(data[1])
    z.append(data[2])
    z.append(data[3])
    z.append(data[4])
    z.append(data[5])
    z.append(passedMeans[7])
    z.append(passedMeans[8])
    z.append(passedMeans[9])

    scaling = 3-n
    w1 = scaling / (n + scaling) # weight for first value
    w2 = 1 / (2 * ( n + scaling)) # weight for all other values
    
    # track the average of the estimated K states so far
    means = passedMeans

    """
    Calculate mean of Gaussian (populates the global predicted means matrix)
    1. Store temporary sigma points
    2. Apply the EOMs to the temporary (stored) sigma points
    2. Calculate the means of sigma points without weights
    4. Calculate the new predicted means by applying predetermined weights
    Let the sigma matrix = the starting sigma point matrix
    """
    predMeans = np.zeros(n)
    # initialize the means array to zeroes

    sigTemp = sigma(means, cov, n, scaling)  # temporary sigma points
    # oldSig = sigTemp

    for i in range(1, n * 2 + 1):  # generate 2N+1 sigma points
        x = EOMs(sigTemp[i])  # use state estimation equations
        g[i] = x  # add the next entry to g matrix
        predMeans = np.add(predMeans,x)  # calculate means of sigma points w/out weights

    # apply weights to predicted means
    predMeans *= w2   # w2 for later weights
    x = EOMs(sigTemp[0])  # calculate EoMs for first sigma point
    g[0] = x  # add first sigma point to first index in g(x)
    predMeans = np.add(predMeans, x*w1)  # w1 for first weight
    
    """
    Calculate predicted covariance of Gaussian
    """
    # for all sigma points
    for i in range(1, n * 2 + 1):
        arr = np.subtract(g[i], predMeans)[np.newaxis]
        # subtract the predicted mean from the transformed sigma points

        arr = np.matmul(arr.transpose(), arr)
        # matrix multiplication: multiply the matrix by itself transposed!
        predCovid = np.add(predCovid, arr)

    arr = np.subtract(g[0], predMeans)[np.newaxis]
    predCovid*=w2
    d = np.matmul(arr.transpose(), arr)*w1  # d: separates out first value

    # add d back to predicted covariance matrix
    predCovid = np.add(predCovid, d)
    # print("PREDICTED COVARIANCE: ", predCovid)
  
    """ 
    Mean to measurement
    """
    #qvmm = getQvmm()
    # create temporary sigma points
    # sigTemp = sensorSigma(z, n, scaling)
    # b = np.random.randint(0,1,size=(10,10))
    # zCov = (b + b.T)/2 #create symmetric covariance
    zCov = [[.1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, .1, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, .1, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, .1, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, .1, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, .1, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, .1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, .1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, .1, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, .1]
    ]
    for i in range(n):
        zCov[i][i] = .2
    # zCov = cov
    # z = means
    sigTemp = sigma(z, zCov, n, scaling)
    
    # pass the sigma point to the h function
    for i in range(1, n * 2 + 1):
        x = H_func(sigTemp[i], q_wmm)
        # x = sigTemp[i] 
        '''works'''
        # transforms sigma points into measurement space
        h[i] = x  # store the calculated point in the h matrix
        meanInMes = np.add(meanInMes, x)  # update mean in measurement mean

    meanInMes *= w2  # weight for later value

    x = H_func(sigTemp[0], q_wmm)  # get first mapped point
    # x = sigTemp[0]
    '''works'''
    h[0] = x  # set the first element in h matrix

    # adjust the means in measurement space for first value
    meanInMes = np.add(meanInMes, [i * w1 for i in x])
    # meanInMes = np.add(meanInMes, (x * w1))


    # print("MEANS IN MEASUREMENT: ", meanInMes)
  
    """
    Creates covariance matrix in measurement space
    """
    for i in range(1, n * 2 + 1):
        arr = np.subtract(h[i], meanInMes)[np.newaxis]
        arr = np.matmul(arr.transpose(), arr)
        covidInMes = np.add(covidInMes, arr)
    
    arr = np.subtract(h[0], meanInMes)[np.newaxis]
    d = np.matmul(arr.transpose(), arr)  #ordering?

    for i in range(m):
        for j in range(m):
            covidInMes[i][j] *= w2
            d[i][j] *= w1
    covidInMes = np.add(covidInMes, d)
    '''remove/add sensor noise here '''
    # covidInMes=np.add(covidInMes,q) 


    # print("COVARIANCE IN MEASUREMENT: ", list(covidInMes), "\n")

    
    '''
    Cross covariance matrix (t): remaking sigma points from new data, unsure if provides advantage
    (this is the cross variance matrix between state space and predicted space)

    Remake sigma points here now that we have new data up to the group
    '''
    # print("\n\nREMAKING SIGMA POINTS\n\n")
    # sig = sigma(means, cov, n, scaling)
    sig = sigTemp
    crossCo = np.zeros((n,m))

    for i in range(1, n * 2 + 1):
        arr1 = np.subtract(sig[i], predMeans)[np.newaxis]
        arr2 = np.subtract(h[i], meanInMes)[np.newaxis]
        arr1 = np.matmul(arr1.transpose(), arr2)  # ordering?
        crossCo = np.add(crossCo, arr1)
        # arr1 = np.subtract(h[i], meanInMes)[np.newaxis]
        # arr2 = np.subtract(sig[i], predMeans)[np.newaxis]
        # arr1 = np.matmul(arr1.transpose(), arr2)  # ordering?
        # crossCo = np.add(crossCo, arr1)
    '''switch ordering??'''

    # arr1 = np.subtract(h[-1], meanInMes)[np.newaxis]
    arr1 = np.subtract(sig[0], predMeans)[np.newaxis]
    arr2 = np.subtract(h[0], meanInMes)[np.newaxis]

    d = np.matmul(arr1.transpose(), arr2)

    for i in range(n):
        for j in range(m):
            crossCo[i][j] *= w2
            d[i][j] *= w1

    crossCo = np.add(crossCo, d)


    """
    Kalman gain and final update
    """
    # print("CROSS COVARIANCE: ", crossCo, "\nINVERTED COVARIANCE: ", np.linalg.inv(covidInMes))
    # calculate kalman gain by multiplying cross covariance matrix and transposed predicted covariance
    # nxm
    kalman = np.matmul(crossCo, np.linalg.inv(covidInMes))
    # print("KALMAN: ", kalman)

    z = z[1:]
    # print("ADDING TO MEANS: ", np.matmul(kalman, np.subtract(z, meanInMes)))
    # updated final mean = predicted + kalman(measurement - predicted in measurement space)
    means = np.add(predMeans, np.matmul(kalman, np.subtract(z, meanInMes)))

    # updated covariance = predicted covariance * (n identity matrix - kalman * cross covariance)

    # this one doesn't work with different n and m for some reason, but second one is wrong i think
    # cov = np.matmul(np.subtract(np.identity(m), np.matmul(kalman, crossCo)), predCovid)
    cov = np.subtract(predCovid, np.matmul(np.matmul(kalman, covidInMes), kalman.transpose()))

    # if don't transpose we could do row col and might be more efficient when put into the mf eoms just an idea
    # could use it for readability at first and then when actual code is put in then change idk

    return [means, cov]