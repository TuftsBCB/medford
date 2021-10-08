Welcome to MEDFORD's documentation!
===================================
.. toctree::
   :maxdepth: 2
   :caption: Contents:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

BagIt as Reference
==================

BagIt, woohoo!
Note to self, the code to re-compile is:

::
   sphinx-build -b html sphinx-docs/docs/source sphinx-docs/docs/build

Also, if restructuredText is breaking, use Ctrl + Shift + P to open keyboard shortcuts. Then, search for all keyboard shortcuts containins restructuredtext.editor.listEditing and delete them.

To get all of this working, I had to install sphinx and sphinx-autobuild on my machine, then install Python Docstring Generator and reStructuredText. Make sure to add this to settings.json:

::
   "autoDocstring.docstringFormat": "sphinx"


.. automodule:: medford_BagIt
    :members:
    :undoc-members:


