[ [ABOUT](README.md) | [SETUP and RUN](SETUP.md) | [CREATE A GAME](CREATE.md) | [TUTORIALS](TUTORIALS.md) | **CONTRIBUTING** ]

# Contributing to LAN-Caster

I'm really glad you're reading this, because this will help us help you. We hope you like LAN-Caster and want to hear from you. The guidelines below help us communicate and work together smoothly.


### **Do you have questions about writing a game, about the LAN-Caster source code, or other questions?**

* **Ensure your question has not already been answered** in the [README](https://github.com/dbakewel/lan-caster/blob/master/README.md) or by searching existing [issues](https://github.com/dbakewel/lan-caster/issues?q=is%3Aissue).

* If you're unable to find the information you need, [open a new issue](https://github.com/dbakewel/lan-caster/issues/new/choose). Be sure to include a **descriptive title** and follow the suggested template as much as possible. Provide as much relative information as possible.


### **Did you find a bug?**

* **Ensure the bug was not already reported** by searching existing open [issues](https://github.com/dbakewel/lan-caster/issues).

* If you're unable to find an issue discussing the problem, [open a new bug report](https://github.com/dbakewel/lan-caster/issues/new?assignees=&labels=&template=bug_report.md&title=). Be sure to include a **descriptive title** and follow the suggested template as much as possible. Provide as much relative information as possible.

### **Do you intend to add a new feature or change an existing one?**

* **Before submitting a pull request**, suggest your change with a [Feature Request](https://github.com/dbakewel/lan-caster/issues/new?assignees=&labels=&template=feature_request.md&title=) so your idea can be discussed. There is no point in writing code when your idea may not be accepted.


### **Submitting Feature Changes or Bug Fixes (Pull Request)**

Please submit a new [GitHub Pull Request](https://github.com/dbakewel/lan-caster/pulls) with a clear list of what you've done.

* **Reference the feature request issue or bug report issue it relates to**. 
* Make sure all of your commits are atomic (one feature per commit). 
* Each commit should clearly describes the change.
* Please follow our coding conventions below.
* Ensure your code is **tested**. Describe what tests you did in the pull request.

**Did you fix whitespace, format code, or make a purely cosmetic change?**

Changes that are cosmetic in nature and do not add anything substantial to the stability, functionality, or testability will generally not be accepted. We know our formatting is not perfect but please only clean up formatting when code needs changing anyway. If this really bugs you then suggest a new feature that is purely for formatting clean up and we can discuss it.

**Coding Conventions**

Start reading the LAN-Caster code and you'll get the hang of it. We are far from perfect and we don't expect you to be.

  * Indent using four spaces (soft tabs)
  * Line length must not exceed 120 characters.
  * Consider the people who will read your code, and make it look nice for them.
  * Beyond that we suggest following [PEP-0008](https://www.python.org/dev/peps/pep-0008/).

The code has been run through autopep8 to perform clean up using the following:
```
cd src
py -m autopep8 -i -v -a --max-line-length 120 --hang-closing --recursive .
```

**Documenting Code**

Look at how the code is commented and uses doc strings and do something similar. This part of PEP 257 should also be followed:

The docstring for a class should summarize its behavior and list the public methods and instance variables. If the class is intended to be subclassed, and has an additional interface for subclasses, this interface should be listed separately (in the docstring). The class constructor should be documented in the docstring for its __init__ method. Individual methods should be documented by their own docstring.

If a class subclasses another class and its behavior is mostly inherited from that class, its docstring should mention this and summarize the differences. Use the verb "override" to indicate that a subclass method replaces a superclass method and does not call the superclass method; use the verb "extend" to indicate that a subclass method calls the superclass method (in addition to its own behavior).



Thanks for reading this!
