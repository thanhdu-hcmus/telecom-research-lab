from lab.eval_graders import grade_task

def grade(output, workspace, expected):
    return grade_task("modeler-derivation", output, workspace, expected)
