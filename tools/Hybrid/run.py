# SIMPLIFIED MISSION MODEL v1
import numpy
from tixi import tixiwrapper
import sys
import math

# ----------------------------------------------------------------------------------------------------------------------

# PRE-PROCESSING (INPUTS)

# CPACS
INFILE = './ToolInput/toolInput.xml'

tixi_h = tixiwrapper.Tixi()
tixi_h.open(INFILE)

print(sys.argv[1])
Perc_Hyb = float(sys.argv[1])                    # [-] Degree of hybridization (0: conventional; 1: full electric) TODO this should be in toolspecific


# Selected Mission Segments
path = '/cpacs/toolspecific/SimplifiedMissionModel/Inputs/MainPhasesDuration'
Dim_vettore = tixi_h.getVectorSize(path)
Phases_duration = tixi_h.getFloatVector(path, Dim_vettore)
Phases_duration = numpy.array(Phases_duration)

# Number of engines
N_engines = tixi_h.getDoubleElement('/cpacs/toolspecific/SimplifiedMissionModel/Inputs/NumberEngines')

# Wing area
S = tixi_h.getDoubleElement('/cpacs/vehicles/aircraft/model/reference/area')

# MTOM
MTOM = tixi_h.getDoubleElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/designMasses/mTOM/mass')

# Cruise altitude
Altitude_cruise = tixi_h.getDoubleElement('/cpacs/toolspecific/SimplifiedPerformanceModel/Inputs/AltitudeCruise')

# Single engine net thrust
path = '/cpacs/toolspecific/SimplifiedPerformanceModel/Outputs/SingleEngineNetThrust'
Dim_vettore = tixi_h.getVectorSize(path)
T = tixi_h.getFloatVector(path, Dim_vettore)  # [kN]
T = numpy.array(T)


# Further inputs
nEM = 0.95                                     # [-] electric motor efficiency
Cl_maxTO = 2.2                                 # [-] maximum lift coefficient in takeoff
nPROP_TO = 0.8                                 # [-] propeller efficiency in takeoff
n_tr = 0.98                                    # [-] mechanical transmission efficiency
g = 9.81                                       # [m/s2] gravitational acceleration
rSL = 1.225                                    # [kg/m3] air density @ Sea Level
Pusers = 50                                    # [kW] electric power required by users in takeoff (approx)
tTO = Phases_duration[0]                       # [h] duration of the takeoff phase
nbattTo = 0.3                                  # [-] battery efficiency in takeoff
EnergyDensityBATT = 150                        # [Wh/kg] energy density of the battery
PowerDensityEM = 0.5                           # [kW/kg] power density of the electric motor

# ----------------------------------------------------------------------------------------------------------------------
# PROCESSING

if Perc_Hyb > 0:
    T_TO = T[0]                                                   # [kN] Thrust required in takeoff
    vTO = 1.2*(2*MTOM*g/S/rSL/Cl_maxTO)**0.5
    Pice = ((1-Perc_Hyb)*T_TO)/(nPROP_TO*n_tr*vTO)/N_engines      # [kW] Single thermal turboprop engine max power
    PelecTO = ((Perc_Hyb*(1-Perc_Hyb))*Pice*N_engines)/nEM        # [kW] Electric power required in Takeoff
    EelecTO = (PelecTO+Pusers)*tTO/nbattTo
    mBATT = EelecTO*1000/EnergyDensityBATT
    mEM = PowerDensityEM*PelecTO
    mMECH = 0.04*Pice*N_engines/0.75
    mHybSys = mBATT+mEM+mMECH
    if tixi_h.checkElement('/cpacs/toolspecific/SimplifiedEngineModel/Outputs/SFCnew') == 0:
        path = '/cpacs/toolspecific/SimplifiedEngineModel/Outputs/SFCnew'
        Dim_vettore = tixi_h.getVectorSize(path)
        SFCnew = tixi_h.getFloatVector(path, Dim_vettore)  # [kN]
        SFCnew = numpy.array(SFCnew)
        SFCnew = SFCnew*0.95
        tixi_h.removeElement('/cpacs/toolspecific/SimplifiedEngineModel/Outputs/SFCnew')
        tixi_h.addFloatVector('/cpacs/toolspecific/SimplifiedEngineModel/Outputs', 'SFCnew', SFCnew, len(SFCnew), '%f')

    # Check constraint (enough ICE power in cruise)
    if Altitude_cruise < 11000:
        r_cruise = 1.225 * math.pow((1 - 6.5 / 288.15 * Altitude_cruise / 1000), 4.25)
    else:
        r_cruise = 0.3639 * math.exp((-9.81 * (Altitude_cruise - 11000)) / (287.3 * 216.65))

    T_cruise_SL = T[2]*1.227/r_cruise
    T_ice = Pice*vTO
    overThrust = T_ice-T_cruise_SL

    if overThrust < 0:
        print("---------------------------------")
        print("ENGINE POWER NOT SUFFICIENT FOR CRUISE!!!!")

    print("---------------------------------")
    print("RESULTS - POWER:")
    print("ICE power: %d [kW]" % Pice)
    print("EM power: %d [kW]" % PelecTO)
    print("Tot power: %d [kW]" % (Pice+PelecTO))
    print("")
    print("RESULTS - MASSES:")
    print("Batt mass: %d [kg]" % mBATT)
    print("EM mass: %d [kg]" % mEM)
    print("Mech mass: %d [kg]" % mMECH)
    print("HEPS mass: %d [kg]" % mHybSys)
    print("---------------------------------")
else:
    mHybSys = 0
    T_TO = T[0]
    vTO = 1.2*(2*MTOM*g/S/rSL/Cl_maxTO)**0.5
    print("---------------------------------")
    print("Conventional propulsion system")
    print("Max T: %d [kN]" % T_TO)
    Pice = (T_TO*vTO/nPROP_TO)/N_engines
    print("Engine power: %d [kW]" % Pice)
    print("---------------------------------")


# ----------------------------------------------------------------------------------------------------------------------
# POST-PROCESSING

if tixi_h.checkElement('/cpacs/toolspecific/HybridTool') == 0:
    tixi_h.createElement('/cpacs/toolspecific', 'HybridTool')

if tixi_h.checkElement('/cpacs/toolspecific/HybridTool/Outputs') == 0:
    tixi_h.createElement('/cpacs/toolspecific/HybridTool', 'Outputs')

# Mission fuel phases
if tixi_h.checkElement('/cpacs/toolspecific/HybridTool/Outputs/mHybridSystem') == 0:
    tixi_h.addDoubleElement('/cpacs/toolspecific/HybridTool/Outputs', 'mHybridSystem', mHybSys, '%f')
else:
    tixi_h.updateDoubleElement('/cpacs/toolspecific/HybridTool/Outputs/mHybridSystem', mHybSys, '%f')

# Thermal engine power
if tixi_h.checkElement('/cpacs/toolspecific/HybridTool/Outputs/ICEpower') == 0:
    tixi_h.addDoubleElement('/cpacs/toolspecific/HybridTool/Outputs', 'ICEpower', Pice, '%f')
else:
    tixi_h.updateDoubleElement('/cpacs/toolspecific/HybridTool/Outputs/ICEpower', Pice, '%f')


# ----------------------------------------------------------------------------------------------------------------------
# System Installation

Installation = 1
if Installation == 1:

    if tixi_h.checkElement('/cpacs/vehicles/aircraft/model/systems') == 0:
        tixi_h.createElement('/cpacs/vehicles/aircraft/model', 'systems')
    if tixi_h.checkElement('/cpacs/vehicles/aircraft/model/systems/genericSystems') == 0:
        tixi_h.createElement('/cpacs/vehicles/aircraft/model/systems', 'genericSystems')

    if tixi_h.checkElement('/cpacs/vehicles/aircraft/model/systems/genericSystems/genericSystem[2]') != 0:
        tixi_h.removeElement('/cpacs/vehicles/aircraft/model/systems/genericSystems/genericSystem[2]')
    if tixi_h.checkElement('/cpacs/vehicles/aircraft/model/systems/genericSystems/genericSystem[1]') != 0:
        tixi_h.removeElement('/cpacs/vehicles/aircraft/model/systems/genericSystems/genericSystem[1]')
# left battery

    battL_x = 15.1
    battL_y = -0.58
    battL_z = -0.41

    n_children=tixi_h.getNumberOfChilds('/cpacs/vehicles/aircraft/model/systems/genericSystems')
    path1 = '/cpacs/vehicles/aircraft/model/systems/genericSystems/genericSystem[1]'
    tixi_h.createElement('/cpacs/vehicles/aircraft/model/systems/genericSystems', 'genericSystem')
    # uID
    tixi_h.addTextAttribute(path1, 'uID', 'batt_L')
    # name
    tixi_h.addTextElement(path1, 'name', 'battery')
    # geometric primitive
    tixi_h.addTextElement(path1, 'geometricBaseType', 'cube')
    # location
    tixi_h.createElement(path1, 'transformation')
    path2 = path1 + '/transformation'
    tixi_h.createElement(path2, 'translation')
    path3 = path2 + '/translation'
    tixi_h.addTextAttribute(path3, 'refType', 'absGlobal')
    tixi_h.addDoubleElement(path3, 'x', battL_x, '%f')
    tixi_h.addDoubleElement(path3, 'y', battL_y, '%f')
    tixi_h.addDoubleElement(path3, 'z', battL_z, '%f')
    # rotation
    tixi_h.createElement(path2, 'rotation')
    path4 = path2 + '/rotation'
    tixi_h.addTextAttribute(path4, 'refType', 'absGlobal')
    tixi_h.addDoubleElement(path4, 'x', 0, '%f')
    tixi_h.addDoubleElement(path4, 'y', 0, '%f')
    tixi_h.addDoubleElement(path4, 'z', 0, '%f')
    # scaling
    tixi_h.addTextElement(path2, 'scaling', '')
    path4 = path2 + '/scaling'
    tixi_h.addDoubleElement(path4, 'x', 1.5, '%f')
    tixi_h.addDoubleElement(path4, 'y', 1, '%f')
    tixi_h.addDoubleElement(path4, 'z', 0.3, '%f')



# left battery

    battR_x = 15.1
    battR_y = 0.58
    battR_z = -0.41

    path1 = '/cpacs/vehicles/aircraft/model/systems/genericSystems/genericSystem[2]'
    if tixi_h.checkElement(path1) != 0:
        tixi_h.removeElement(path1)
    tixi_h.createElement('/cpacs/vehicles/aircraft/model/systems/genericSystems', 'genericSystem')
    # uID
    tixi_h.addTextAttribute(path1, 'uID', 'batt_R')
    # name
    tixi_h.addTextElement(path1, 'name', 'battery')
    # geometric primitive
    tixi_h.addTextElement(path1, 'geometricBaseType', 'cube')
    # location
    tixi_h.createElement(path1, 'transformation')
    path2 = path1 + '/transformation'
    tixi_h.createElement(path2, 'translation')
    path3 = path2 + '/translation'
    tixi_h.addTextAttribute(path3, 'refType', 'absGlobal')
    tixi_h.addDoubleElement(path3, 'x', battR_x, '%f')
    tixi_h.addDoubleElement(path3, 'y', battR_y, '%f')
    tixi_h.addDoubleElement(path3, 'z', battR_z, '%f')
    # rotation
    tixi_h.createElement(path2, 'rotation')
    path4 = path2 + '/rotation'
    tixi_h.addTextAttribute(path4, 'refType', 'absGlobal')
    tixi_h.addDoubleElement(path4, 'x', 0, '%f')
    tixi_h.addDoubleElement(path4, 'y', 0, '%f')
    tixi_h.addDoubleElement(path4, 'z', 0, '%f')
    # scaling
    tixi_h.addTextElement(path2, 'scaling', '')
    path4 = path2 + '/scaling'
    tixi_h.addDoubleElement(path4, 'x', 1.5, '%f')
    tixi_h.addDoubleElement(path4, 'y', 1, '%f')
    tixi_h.addDoubleElement(path4, 'z', 0.3, '%f')

file_out = 'ToolOutput/toolOutput.xml'
tixi_h.saveDocument(file_out)
tixi_h.close()
