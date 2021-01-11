# SIMPLIFIED PERFORMANCE MODEL v1
import math
from tixi import tixiwrapper
import numpy


# 08.08.2018 - Script creation


# ----------------------------------------------------------------------------------------------------------------------
# PRE-PROCESSING (INPUTS)
Sigma = 1                                           # [-] ratio among air density at SL and air density of the airfield
g = 9.81                                            # [m/s^2] gravitational acceleration
k_descent = 0.47                                    # [-] power ratio in descent (from Artur's Engine Deck)
k_landing = 0.13                                    # [-] power ratio in landing (from Artur's Engine Deck)

# CPACS
INFILE = './ToolInput/toolInput.xml'
tixi_h = tixiwrapper.Tixi()
tixi_h.open(INFILE) 


# MTOM 
MTOM = tixi_h.getDoubleElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/designMasses/mTOM/mass')

# Wing area
S = tixi_h.getDoubleElement('/cpacs/vehicles/aircraft/model/reference/area')

# TOFL
TO_length = tixi_h.getDoubleElement('/cpacs/toolspecific/SimplifiedPerformanceModel/Inputs/TOFL')

# Cl @ takeoff
Cl_takeoff = tixi_h.getDoubleElement('/cpacs/toolspecific/SimplifiedPerformanceModel/Inputs/Cl_takeoff')

# Number of engines
N_engines = tixi_h.getDoubleElement('/cpacs/toolspecific/SimplifiedPerformanceModel/Inputs/NumberEngines')

# Speed during climb
V_climb = tixi_h.getDoubleElement('/cpacs/toolspecific/SimplifiedPerformanceModel/Inputs/V_climb')

# Vertical speed
Vvert = tixi_h.getDoubleElement('/cpacs/toolspecific/SimplifiedPerformanceModel/Inputs/VerticalSpeed')

# Altitude climb
Altitude_climb = tixi_h.getDoubleElement('/cpacs/toolspecific/SimplifiedPerformanceModel/Inputs/AltitudeClimb')

# Altitude cruise
Altitude_cruise = tixi_h.getDoubleElement('/cpacs/toolspecific/SimplifiedPerformanceModel/Inputs/AltitudeCruise')

# Cruise speed
V_cruise = tixi_h.getDoubleElement('/cpacs/toolspecific/SimplifiedPerformanceModel/Inputs/SpeedCruise')

# GET CL and CD from CPACS
XpathAeroPerformanceMap = '/cpacs/vehicles/aircraft/model/analyses/aeroPerformanceMap'
nMN = tixi_h.getVectorSize(XpathAeroPerformanceMap+'/machNumber')
nRN = tixi_h.getVectorSize(XpathAeroPerformanceMap+'/reynoldsNumber')
nAOY = tixi_h.getVectorSize(XpathAeroPerformanceMap+'/angleOfYaw')
nAOA = tixi_h.getVectorSize(XpathAeroPerformanceMap+'/angleOfAttack')

nCases = nMN*nRN*nAOY*nAOA

Mach_all = tixi_h.getFloatVector(XpathAeroPerformanceMap+'/machNumber', nMN)
Mach_all = numpy.array(Mach_all)
Re_all = tixi_h.getFloatVector(XpathAeroPerformanceMap+'/reynoldsNumber', nRN)
Re_all = numpy.array(Re_all)

Cd_all = tixi_h.getArray(XpathAeroPerformanceMap, 'cdT', nCases)
Cl_all = tixi_h.getArray(XpathAeroPerformanceMap, 'clT', nCases)
Cfx_all = tixi_h.getArray(XpathAeroPerformanceMap, 'cfx', nCases)
Cfy_all = tixi_h.getArray(XpathAeroPerformanceMap, 'cfy', nCases)
Cfz_all = tixi_h.getArray(XpathAeroPerformanceMap, 'cfz', nCases)

alpha_all = tixi_h.getFloatVector(XpathAeroPerformanceMap+'/angleOfAttack', nAOA)
alpha_all = numpy.array(alpha_all)
beta_all = 0 # tixi_h.getFloatVector(XpathAeroPerformanceMap+'/angleOfYaw', nAOY)
beta_all = numpy.array(beta_all)

cont_mach = 0
caso = 0
Aero_matrix = numpy.zeros((nMN, 6, nAOA))
contReynolds = 1

while caso < len(Cd_all):
    for alfa in range(nAOA):
        if contReynolds == 1:
            Aero_matrix[cont_mach][0][alfa] = Mach_all[cont_mach]
            Aero_matrix[cont_mach][1][alfa] = Cl_all[caso]
            Aero_matrix[cont_mach][2][alfa] = Cd_all[caso]

            Aero_matrix[cont_mach][3][alfa] = Cfx_all[caso]
            Aero_matrix[cont_mach][4][alfa] = Cfy_all[caso]
            Aero_matrix[cont_mach][5][alfa] = Cfz_all[caso]

            b2w = numpy.array([[math.cos(math.radians(beta_all))*math.cos(math.radians(alpha_all[alfa])),
                                math.sin(math.radians(beta_all)),
                                math.cos(math.radians(beta_all))*math.sin(math.radians(alpha_all[alfa]))],
                               [-math.sin(math.radians(beta_all))*math.cos(math.radians(alpha_all[alfa])),
                                math.cos(math.radians(beta_all)),
                                -math.sin(math.radians(beta_all))*math.sin(math.radians(alpha_all[alfa]))],
                               [-math.sin(math.radians(alpha_all[alfa])), 0, math.cos(math.radians(alpha_all[alfa]))]])
            Trasf = numpy.matmul(b2w, numpy.array([[Aero_matrix[cont_mach][3][alfa]], [Aero_matrix[cont_mach][4][alfa]],
                                                   [Aero_matrix[cont_mach][5][alfa]]]))

            Aero_matrix[cont_mach][3][alfa] = Trasf[0]
            Aero_matrix[cont_mach][4][alfa] = Trasf[1]
            Aero_matrix[cont_mach][5][alfa] = Trasf[2]

        caso = caso+1
    contReynolds = contReynolds+1
    if contReynolds == nRN+1:
        contReynolds = 1
        cont_mach = cont_mach + 1


print("Input from cpacs completed")


# ----------------------------------------------------------------------------------------------------------------------
# PROCESSING

# Takeoff
T_takeoff = MTOM/(TO_length*Cl_takeoff*Sigma)*2.33*(MTOM/S)*g/1000/N_engines  # [kN] thrust per engine at takeoff

# Climb
if Altitude_climb < 11000:
    T_climb = 273.15-0.0065*Altitude_climb
    r_climb = 1.225*math.pow((1-6.5/288.15*Altitude_climb/1000), 4.25)
else:
    r_climb = 0.3639*math.exp((-9.81*(Altitude_climb-11000))/(287.3*216.65))
    T_climb = -56.5+273.15

c_climb = math.sqrt(1.4*287*T_climb)
Mach_climb = V_climb/c_climb
Cl_climb = ((2*g*MTOM/S)/(r_climb*(V_climb**2)))

INT1 = numpy.zeros(nMN)
for n_mach in range(nMN):
    INT1[n_mach] = numpy.interp(Cl_climb, Aero_matrix[n_mach, 5, :], Aero_matrix[n_mach, 3, :])

Cd_climb = numpy.interp(Mach_climb, Mach_all, INT1)
T_climb = (0.5*r_climb*V_climb**2*S*Cd_climb+Vvert)/1000/N_engines  # [kN] thrust per engine in climb

# Cruise
if Altitude_cruise < 11000:
    r_cruise = 1.225*math.pow((1-6.5/288.15*Altitude_cruise/1000), 4.25)
    T_cruise = 273.15-0.0065*Altitude_cruise
else:
    r_cruise = 0.3639*math.exp((-9.81*(Altitude_cruise-11000))/(287.3*216.65))
    T_cruise = -56.5+273.15

Cl_cruise = ((2*g*MTOM/S)/(r_cruise*(V_cruise**2)))
c_cruise = math.sqrt(1.4*287*T_cruise)
Mach_cruise = V_cruise/c_cruise
for n_mach in range(nMN):
    INT1[n_mach] = numpy.interp(Cl_cruise, Aero_matrix[n_mach, 5, :], Aero_matrix[n_mach, 3, :])

Cd_cruise = numpy.interp(Mach_cruise, Mach_all, INT1)
T_cruise = (0.5*r_cruise*math.pow(V_cruise, 2)*S*Cd_cruise)/1000/N_engines  # [kN] thrust per engine in cruise

# Descent
T_descent = k_descent*T_takeoff  # [kN] thrust per engine in descent

# Landing
T_landing = k_landing*T_takeoff  # [kN] thrust per engine in descent

# Save into a vector
Thrust = [T_takeoff, T_climb, T_cruise, T_descent, T_landing]

print("Processing completed")


# ----------------------------------------------------------------------------------------------------------------------
# POST-PROCESSING
if tixi_h.checkElement('/cpacs/toolspecific/SimplifiedPerformanceModel') == 0:
    tixi_h.createElement('/cpacs/toolspecific', 'SimplifiedPerformanceModel')

if tixi_h.checkElement('/cpacs/toolspecific/SimplifiedPerformanceModel/Outputs') == 0:
    tixi_h.createElement('/cpacs/toolspecific/SimplifiedPerformanceModel', 'Outputs')


# Thrust
if tixi_h.checkElement('/cpacs/toolspecific/SimplifiedPerformanceModel/Outputs/SingleEngineNetThrust') == 1:
    tixi_h.removeElement('/cpacs/toolspecific/SimplifiedPerformanceModel/Outputs/SingleEngineNetThrust')
tixi_h.addFloatVector('/cpacs/toolspecific/SimplifiedPerformanceModel/Outputs', 'SingleEngineNetThrust', Thrust,
                      len(Thrust), '%f')


# Engine max thrust
if tixi_h.checkElement('/cpacs/vehicles/engines') == 0:
    tixi_h.createElement('/cpacs/vehicles', 'engines')

if tixi_h.checkElement('/cpacs/vehicles/engines/engine') == 0:
    tixi_h.createElement('/cpacs/vehicles/engines', 'engine')
	
if tixi_h.checkElement('/cpacs/vehicles/engines/engine[1]/analysis') == 0:
    tixi_h.createElement('/cpacs/vehicles/engines/engine', 'analysis')
	
if tixi_h.checkElement('/cpacs/vehicles/engines/engine[1]/analysis/thrust00') == 0:
    tixi_h.addDoubleElement('/cpacs/vehicles/engines/engine[1]/analysis', 'thrust00', T_takeoff, '%f')
else:
    tixi_h.updateDoubleElement('/cpacs/vehicles/engines/engine[1]/analysis/thrust00', T_takeoff, '%f')

file_out = './ToolOutput/ToolOutput.xml'
tixi_h.saveDocument(file_out)
tixi_h.close()

print("Tool execution completed")
