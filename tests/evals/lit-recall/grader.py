from lab.eval_graders import grade_task

def grade(output, workspace, expected):
    return grade_task('lit-recall', output, workspace, expected)
