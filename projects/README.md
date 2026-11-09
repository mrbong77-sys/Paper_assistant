# projects/

`python -m pa new <slug>` creates your projects here. Everything in this folder except this README is ignored by git,
so your manuscripts, data and reviews never go to the public Paper Assistant repository.

To keep projects under version control, point `PA_PROJECTS` to a folder in a **private** repository:

    export PA_PROJECTS=~/research/my-papers        # PowerShell: $env:PA_PROJECTS = "D:\research\my-papers"

The worked example lives in `examples/demo_project/`.
