from lab.eval_graders import grade_task

def grade(output, workspace, expected):
    return grade_task("critic-planted-flaws", output, workspace, expected)
