import os
import ScriptEnv

OUTPUT_DIR = "/home/solarstatiion/aedt-mcp/projects/dr_strange_d7_isolation_20260803"
PROJECT_PATH = os.path.join(OUTPUT_DIR, "d7_isolation_tuning.aedt")
DESIGN_NAME = "600MHz_slot couple_F4B_1X2_3"

ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
project = oDesktop.OpenProject(PROJECT_PATH)
design = project.SetActiveDesign(DESIGN_NAME)
design.SetVariableValue("mx", "210mm")
analysis = design.GetModule("AnalysisSetup")
analysis.EditSetup("Setup1", ["NAME:Setup1", "SolveType:=", "Single", "Frequency:=", "600MHz", "MaxDeltaS:=", 0.02, "UseMatrixConv:=", False, "MaximumPasses:=", 20, "MinimumPasses:=", 1, "MinimumConvergedPasses:=", 1, "PercentRefinement:=", 30, "IsEnabled:=", True, ["NAME:MeshLink", "ImportMesh:=", False], "BasisOrder:=", 1, "DoLambdaRefine:=", True, "DoMaterialLambda:=", True, "SetLambdaTarget:=", False, "Target:=", 0.3333, "UseMaxTetIncrease:=", False, "PortAccuracy:=", 2, "UseABCOnPort:=", False, "SetPortMinMaxTri:=", False, "DrivenSolverType:=", "Direct Solver", "EnhancedLowFreqAccuracy:=", False, "SaveRadFieldsOnly:=", False, "SaveAnyFields:=", True, "IESolverType:=", "Auto", "LambdaTargetForIESolver:=", 0.15, "UseDefaultLambdaTgtForIESolver:=", True, "IE Solver Accuracy:=", "Balanced"])
project.Save()
design.Analyze("Setup1")
project.Save()
oDesktop.CloseProject(project.GetName())
