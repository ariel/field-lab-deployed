"""Guard source files that local builds can see but a Git clone might omit."""
from pathlib import Path
import subprocess,unittest
ROOT=Path(__file__).resolve().parents[1]
class SourceDistribution(unittest.TestCase):
 def test_swift_source_graph_is_present_and_git_tracked(self):
  required=['native-progress/Package.swift','ditnotes/native/feature_select.swift']
  required += ['native-progress/Sources/IndexerProgress/'+p for p in ['App/IndexerProgressApp.swift','Models/ProgressStatus.swift','Services/ProgressClient.swift','Views/ContentView.swift']]
  for name in required:
   self.assertTrue((ROOT/name).is_file(),name+' missing from distribution')
   if (ROOT/'.git').exists():
    result=subprocess.run(['git','ls-files','--error-unmatch','--',name],cwd=ROOT,capture_output=True,text=True)
    self.assertEqual(result.returncode,0,name+' is visible locally but absent from Git')
 def test_git_excludes_root_model_weights_but_not_nested_swift_models(self):
  if not (ROOT/'.git').exists():self.skipTest('Archive has no Git metadata')
  ignored=subprocess.run(['git','check-ignore','--no-index','models/weights.safetensors'],cwd=ROOT,capture_output=True)
  self.assertEqual(ignored.returncode,0)
  source=subprocess.run(['git','check-ignore','--no-index','native-progress/Sources/IndexerProgress/Models/ProgressStatus.swift'],cwd=ROOT,capture_output=True)
  self.assertEqual(source.returncode,1,'Model-weight exclusion swallowed Swift source')
if __name__=='__main__':unittest.main()
