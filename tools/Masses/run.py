# SIMPLIFIED MASS ESTIMATION MODEL v1
from tixi import tixiwrapper
from tigl import tiglwrapper

# ----------------------------------------------------------------------------------------------------------------------


# CPACS
INFILE = './ToolInput/toolInput.xml'
tixi_h = tixiwrapper.Tixi()
tigl = tiglwrapper.Tigl()
tixi_h.open(INFILE)
tigl.open(tixi_h, '')

# ----------------------------------------------------------------------------------------------------------------------
# FIRST PART

mEngineDry = tixi_h.getDoubleElement('/cpacs/toolspecific/SimplifiedEngineModel/Outputs/EngineDryMass')
mEngine = mEngineDry * 1.24
mEngines = mEngine * 2

if tixi_h.checkElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits') == 0:
    tixi_h.createElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM', 'mPowerUnits')
if tixi_h.checkElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits/mEngines') == 0:
    tixi_h.createElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits','mEngines')
if tixi_h.checkElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits/mEngines/mEngine[1]') == 0:
    tixi_h.createElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits/mEngines','mEngine')
if tixi_h.checkElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits/mEngines/mEngine[1]/massDescription') == 0:
    tixi_h.createElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits/mEngines/mEngine[1]','massDescription')
if tixi_h.checkElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits/mEngines/mEngine[1]/massDescription/mass') == 0:
    tixi_h.createElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits/mEngines/mEngine[1]/massDescription','mass')
if tixi_h.checkElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits/mEngines/mEngine[2]') == 0:
    tixi_h.createElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits/mEngines','mEngine')
if tixi_h.checkElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits/mEngines/mEngine[2]/massDescription') == 0:
    tixi_h.createElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits/mEngines/mEngine[2]','massDescription')
if tixi_h.checkElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits/mEngines/mEngine[2]/massDescription/mass') == 0:
    tixi_h.createElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits/mEngines/mEngine[2]/massDescription','mass')
if tixi_h.checkElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits/massDescription') == 0:
    tixi_h.createElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits','massDescription')
if tixi_h.checkElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits/massDescription/mass') == 0:
    tixi_h.createElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits/massDescription','mass')
	
tixi_h.updateTextElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits/mEngines'
                         '/mEngine[1]/massDescription/mass', str(mEngine))
tixi_h.updateTextElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits/mEngines'
                         '/mEngine[2]/massDescription/mass', str(mEngine))
tixi_h.updateTextElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits'
                         '/massDescription/mass', str(mEngines))

# ----------------------------------------------------------------------------------------------------------------------
# SECOND PART

# Code in place of CMUneo
mEngine = tixi_h.getDoubleElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mPowerUnits'
                                  '/mEngines/mEngine[1]/massDescription/mass')
mPropulsion = mEngine * 2

Wing_mass = 0
NumberOfWings = tigl.getWingCount()
for w in range(NumberOfWings):
    w = w + 1
    path = '/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mStructure/mWingsStructure' \
           '/mWingStructure[%d]/massDescription/mass' % w
    Wing_mass = Wing_mass + tixi_h.getDoubleElement(path)

Fuse_mass = tixi_h.getDoubleElement(
    '/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mStructure/mFuselagesStructure'
    '/mFuselageStructure/massDescription/mass')
Pylon_mass = tixi_h.getDoubleElement(
    '/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mStructure/mPylons/massDescription/mass')
Landing_gear_mass = tixi_h.getDoubleElement(
    '/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mStructure/mLandingGears/massDescription/mass')

mStructure = Wing_mass + Fuse_mass + Pylon_mass + Landing_gear_mass

mFurnishing = tixi_h.getDoubleElement(
    '/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mFurnishing/massDescription/mass')
mSystems = tixi_h.getDoubleElement(
    '/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/mSystems/massDescription/mass')
mOperatings = tixi_h.getDoubleElement(
    '/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mOperatorItems/massDescription/mass')
mHybrid = tixi_h.getDoubleElement('/cpacs/toolspecific/HybridTool/Outputs/mHybridSystem')

mEM = mPropulsion + mFurnishing + mStructure + mSystems + mHybrid
mOEM = mEM + mOperatings

try:
    tixi_h.updateDoubleElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/massDescription/mass',
                               mEM, '%f')
except:
    tixi_h.createElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM', 'massDescription')
    tixi_h.addDoubleElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/mEM/massDescription', 'mass',
                            mEM, '%f')

tixi_h.updateDoubleElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/mOEM/massDescription/mass', mOEM,
                           '%f')

mPayload = tixi_h.getDoubleElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/payload/massDescription/mass')
mFuelMission = tixi_h.getDoubleElement('/cpacs/toolspecific/SimplifiedMissionModel/Outputs/MissionFuel')
mFuelReserve = tixi_h.getDoubleElement('/cpacs/toolspecific/SimplifiedMissionModel/Outputs/FuelReserves')

mTOM = sum([mFuelMission, mFuelReserve, mPayload, mOEM])

if tixi_h.checkElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/designMasses') == 0:
    tixi_h.createElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown', 'designMasses')
if tixi_h.checkElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/designMasses/mTOM') == 0:
    tixi_h.createElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/designMasses','mTOM')
if tixi_h.checkElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/designMasses/mTOM/mass') == 0:
    tixi_h.createElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/designMasses/mTOM','mass')
	
tixi_h.updateTextElement('/cpacs/vehicles/aircraft/model/analyses/massBreakdown/designMasses/mTOM/mass', str(mTOM))


file_out = 'ToolOutput/toolOutput.xml'
tixi_h.saveDocument(file_out)
tixi_h.close()
