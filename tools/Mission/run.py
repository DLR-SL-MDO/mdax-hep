# SIMPLIFIED MISSION MODEL v1
import numpy
from tixi import tixiwrapper


# ----------------------------------------------------------------------------------------------------------------------
# PRE-PROCESSING (INPUTS)

# CPACS
INFILE = './ToolInput/toolInput.xml'
tixi_h = tixiwrapper.Tixi()
tixi_h.open(INFILE)

# Selected Mission Segments
path = '/cpacs/toolspecific/SimplifiedMissionModel/Inputs/MainPhasesDuration'
Dim_vettore = tixi_h.getVectorSize(path)
Phases_duration = tixi_h.getFloatVector(path, Dim_vettore)
Phases_duration = numpy.array(Phases_duration)

# Number of engines
N_engines = tixi_h.getDoubleElement('/cpacs/toolspecific/SimplifiedMissionModel/Inputs/NumberEngines')

# Engine SFC (input from Simplified Engine Model)
path = '/cpacs/toolspecific/SimplifiedEngineModel/Outputs/SFCnew'
Dim_vettore = tixi_h.getVectorSize(path)
SFC = tixi_h.getFloatVector(path, Dim_vettore)  # [lb/lbf/h]
SFC = numpy.array(SFC)

# Single engine net thrust
path = '/cpacs/toolspecific/SimplifiedPerformanceModel/Outputs/SingleEngineNetThrust'
Dim_vettore = tixi_h.getVectorSize(path)
T = tixi_h.getFloatVector(path, Dim_vettore)  # [kN]
T = numpy.array(T)

# Percentage of fuel reserves
perc_Res = tixi_h.getDoubleElement('/cpacs/toolspecific/SimplifiedMissionModel/Inputs/PercentageReserves')


# ----------------------------------------------------------------------------------------------------------------------
# PROCESSING
Mission_Fuel_phases = SFC*T/9.81*1000*Phases_duration*N_engines   # [kg]
Mission_Fuel = numpy.sum(Mission_Fuel_phases)                     # [kg]
Reserve_Fuel = perc_Res*Mission_Fuel                              # [kg]
Total_Fuel = Mission_Fuel+Reserve_Fuel                            # [kg]


# ----------------------------------------------------------------------------------------------------------------------
# POST-PROCESSING

if tixi_h.checkElement('/cpacs/toolspecific/SimplifiedMissionModel') == 0:
    tixi_h.createElement('/cpacs/toolspecific', 'SimplifiedMissionModel')

if tixi_h.checkElement('/cpacs/toolspecific/SimplifiedMissionModel/Outputs') == 0:
    tixi_h.createElement('/cpacs/toolspecific/SimplifiedMissionModel', 'Outputs')

# Mission fuel phases
if tixi_h.checkElement('/cpacs/toolspecific/SimplifiedMissionModel/Outputs/MissionFuelPhases') == 1:
    tixi_h.removeElement('/cpacs/toolspecific/SimplifiedMissionModel/Outputs/MissionFuelPhases')
tixi_h.addFloatVector('/cpacs/toolspecific/SimplifiedMissionModel/Outputs', 'MissionFuelPhases', Mission_Fuel_phases,
                      len(Mission_Fuel_phases), '%f')

# Mission fuel phases
if tixi_h.checkElement('/cpacs/toolspecific/SimplifiedMissionModel/Outputs/MissionFuel') == 0:
    tixi_h.addDoubleElement('/cpacs/toolspecific/SimplifiedMissionModel/Outputs', 'MissionFuel', Mission_Fuel, '%f')
else:
    tixi_h.updateDoubleElement('/cpacs/toolspecific/SimplifiedMissionModel/Outputs/MissionFuel', Mission_Fuel, '%f')

# Fuel Reserves
if tixi_h.checkElement('/cpacs/toolspecific/SimplifiedMissionModel/Outputs/FuelReserves') == 0:
    tixi_h.addDoubleElement('/cpacs/toolspecific/SimplifiedMissionModel/Outputs', 'FuelReserves', Reserve_Fuel, '%f')
else:
    tixi_h.updateDoubleElement('/cpacs/toolspecific/SimplifiedMissionModel/Outputs/FuelReserves', Reserve_Fuel, '%f')

# Total fuel
if tixi_h.checkElement('/cpacs/toolspecific/SimplifiedMissionModel/Outputs/TotalFuel') == 0:
    tixi_h.addDoubleElement('/cpacs/toolspecific/SimplifiedMissionModel/Outputs', 'TotalFuel', Total_Fuel, '%f')
else:
    tixi_h.updateDoubleElement('/cpacs/toolspecific/SimplifiedMissionModel/Outputs/TotalFuel', Total_Fuel, '%f')


file_out = 'ToolOutput/toolOutput.xml'
tixi_h.saveDocument(file_out)
tixi_h.close()
