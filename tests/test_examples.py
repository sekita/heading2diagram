import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class ExampleOutputTests(unittest.TestCase):
    rootDir = Path(__file__).resolve().parents[1]
    programPath = rootDir / "heading2diagram.py"
    examplesDir = rootDir / "examples"

    cases = [
        ("example1.md", "out1_hier-block.md", ["-t", "hier-block"]),
        ("example1.md", "out1_hier-flow.md", ["-t", "hier-flow"]),
        ("example1.md", "out1_hier-mind.md", ["-t", "hier-mind"]),
        ("example1.md", "out1_struct-flow_tight.md", ["-t", "struct-flow", "--layout", "tight"]),
        ("example2.md", "out2_hier-block_LR_tight.md", ["-t", "hier-block", "--direction", "LR", "--layout", "tight"]),
        ("example2.md", "out2_hier-flow_LR.md", ["-t", "hier-flow", "--direction", "LR"]),
        ("example2.md", "out2_hier-mindlabel_LR.md", ["-t", "hier-mindlabel", "--direction", "LR"]),
        ("example2.md", "out2_struct-flow_tight.md", ["-t", "struct-flow", "--layout", "tight"]),
        ("example3.md", "out3_fishBone.md", ["-t", "fishBone"]),
        ("example3.md", "out3_hier-flow_RL_thickArrow_arrowReverse.md", ["-t", "hier-flow", "--direction", "RL", "--line", "thickArrow", "--arrowDirection", "reverse"]),
        ("example4.md", "out4_venn.md", ["-t", "venn"]),
        ("example5.md", "out5_table1c.md", ["-t", "table1c"]),
        ("example6.md", "out6_quadrant.md", ["-t", "quadrant"]),
        ("example7.md", "out7_pie.md", ["-t", "pie"]),
    ]

    def testReferenceOutputs(self):
        with tempfile.TemporaryDirectory() as tempDir:
            tempPath = Path(tempDir)
            for inputName, outputName, optionArgs in self.cases:
                with self.subTest(output=outputName):
                    generatedPath = tempPath / outputName
                    command = [
                        sys.executable,
                        str(self.programPath),
                        str(self.examplesDir / inputName),
                        *optionArgs,
                        "-o",
                        str(generatedPath),
                    ]
                    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
                    self.assertEqual(result.returncode, 0, msg=result.stderr)
                    expectedText = (self.examplesDir / outputName).read_text(encoding="utf-8")
                    actualText = generatedPath.read_text(encoding="utf-8")
                    self.assertEqual(actualText, expectedText)


if __name__ == "__main__":
    unittest.main()
