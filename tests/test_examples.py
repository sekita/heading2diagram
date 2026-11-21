import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


def buildCases(suffix, outPrefix):
    """日本語（suffix=''）・英語（suffix='_en'）で共通のテストケースを作る。"""
    def inputName(number):
        return f"example{number}{suffix}.md"

    def outputName(number, name):
        return f"out{number}{outPrefix}_{name}.md"

    return [
        (inputName(1), outputName(1, "hier-block"), ["-t", "hier-block"]),
        (inputName(1), outputName(1, "hier-flow"), ["-t", "hier-flow"]),
        (inputName(1), outputName(1, "hier-mind"), ["-t", "hier-mind"]),
        (inputName(1), outputName(1, "struct-flow_tight"), ["-t", "struct-flow", "--layout", "tight"]),
        (inputName(2), outputName(2, "hier-block_LR_tight"), ["-t", "hier-block", "--direction", "LR", "--layout", "tight"]),
        (inputName(2), outputName(2, "hier-flow_LR"), ["-t", "hier-flow", "--direction", "LR"]),
        (inputName(2), outputName(2, "hier-mindlabel_LR"), ["-t", "hier-mindlabel", "--direction", "LR"]),
        (inputName(2), outputName(2, "struct-flow_tight"), ["-t", "struct-flow", "--layout", "tight"]),
        (inputName(3), outputName(3, "fishBone"), ["-t", "fishBone"]),
        (inputName(3), outputName(3, "hier-flow_RL_thickArrow_arrowReverse"), ["-t", "hier-flow", "--direction", "RL", "--line", "thickArrow", "--arrowDirection", "reverse"]),
        (inputName(4), outputName(4, "venn"), ["-t", "venn"]),
        (inputName(5), outputName(5, "table1c"), ["-t", "table1c"]),
        (inputName(6), outputName(6, "quadrant"), ["-t", "quadrant"]),
        (inputName(7), outputName(7, "pie"), ["-t", "pie"]),
        (inputName(8), outputName(8, "star"), ["-t", "star"]),
        (inputName(8), outputName(8, "star_degree30_dotted"), ["-t", "star", "--degree", "30", "--line", "dotted"]),
    ]


class ExampleOutputTests(unittest.TestCase):
    rootDir = Path(__file__).resolve().parents[1]
    programPath = rootDir / "heading2diagram.py"
    examplesDir = rootDir / "examples"

    japaneseCases = buildCases("", "")
    englishCases = buildCases("_en", "_en")

    def checkCases(self, cases):
        with tempfile.TemporaryDirectory() as tempDir:
            tempPath = Path(tempDir)
            for inputName, outputName, optionArgs in cases:
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

    def testJapaneseReferenceOutputs(self):
        self.checkCases(self.japaneseCases)

    def testEnglishReferenceOutputs(self):
        self.checkCases(self.englishCases)


if __name__ == "__main__":
    unittest.main()
