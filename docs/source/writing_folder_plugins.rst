Writing Plugins
===============

For a working example of a folder plugin, check out
`Jirafs-Pandoc's Github Repository <https://github.com/coddingtonbear/jirafs-pandoc>`_.

.. _entry_points:

Setuptools Entrypoint
---------------------

* Add a setuptools entrypoint to your plugin's ``setup.py``::

    entry_points={
      'jirafs_plugins': [
          "my_plugin_name = module.path:ClassName"
      ]
    }

* Write a subclass of ``jirafs.plugin.Plugin`` implementing
  one or more methods using the interface described in `Folder Plugin API`_.

Folder Plugin API
-----------------

The following properties **must** be defined:

* ``MIN_VERSION``: The string version number representing the minimum version
  of Jirafs that this plugin will work with.
* ``MAX_VERSION``: The string version number representing the maximum version
  of Jirafs that this plugin is compatible with.  Note: Jirafs uses semantic
  versioning, so you may set this value accordingly.

The following methods may be defined for altering Jirafs behavior.

Alteration Methods
~~~~~~~~~~~~~~~~~~

* ``alter_filter_ignored_files(filename_list)``:

  * Further filter the list of files to be processed by reducing this
    list further.
  * Return further filtered ``filename_list``.

* ``alter_new_comment(comment)``:

  * Alter the returned comment.
  * Return an altered ``comment`` string.

* ``alter_remotely_changed(filename_list)``:

  * Alter the list of remotely changed files if necessary.  
  * Return an altered ``filename_list``.

* ``alter_file_upload((filename, file_like_object, ))``:

  * Alter a file pre-upload.
  * Return a new tuple of ``(filename, file_like_object)``.

* ``alter_file_download((filename, file_content, ))``:

  * Alter a file pre-save from JIRA.
  * Return a new tuple of ``(filename, file_like_object)``.

* ``alter_get_remote_file_metadata(file_metadata)``:

  * Alter remote file metadata dictionary after retrieval.
  * Return an altered ``file_metadata`` dictionary.

* ``alter_set_remote_file_metadata(file_metadata)``:

  * Alter remote file metadata dictionary before storage.
  * Return an altered ``file_metadata`` dictionary.

* ``alter_status_dict(status_dict)``:

  * Executed after running ``status``.
  * ``status_dict`` dictionary (see tests and source for details):

    * ``uncommitted``: A dictionary containing uncommitted changes.
    * ``ready``: A dictionary of changes ready for submission to JIRA.
    * ``up_to_date``: A boolean value indicating whether the current
      ``master`` branch is up-to-date with changes fetched in the
      ``jira`` branch.

  * Return an altered ``status_dict``.


.. note::

   For technical reasons, both ``alter_file_upload`` and
   ``alter_file_download`` accept a single tuple argument containing
   the filename and object rather than two arguments.

Pre/Post Command Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All commands (including user-installed commands) can have plugins altering
their behavior by defining ``pre_*COMMAND*`` and ``post_*COMMAND*`` methods.
For the below, please replace ``*COMMAND*`` with the command your plugin
would like to alter the behavior of.

* ``pre_*COMMAND*(**kwargs)``:

  * Executed before handling ``*COMMAND*``.  Receives (as ``**kwargs``)
    all parameters that will be passed-in to the underlying command. 
  * You may alter the parameters that will be passed-in to the underlying
    command by returning a new or altered ``**kwargs`` dictionary.
  * Return ``None`` or the original ``**kwargs`` dictionary to pass
    original arguments to the command without alteration.

* ``post_*COMMAND*(returned)``:

  * Executed after handling ``*COMMAND*``.  Receives as an argument the
    result returned by the underlying command.

.. note::

   Although the return values of commands are not in the scope of this
   specification, many commands return a ``jirafs.utils.PostStatusResponse``
   instance.

   Such an instance is a named tuple containing two properties:

   * (bool) ``new``: Whether the command's action had an effect on the
     underlying git repository.
   * (string) ``hash``: The hash of the relevant repository branch's head
     commit following the action.

Properties
~~~~~~~~~~

The plugin will have the following properties and methods at its disposal:

* ``self.ticketfolder``: An instance of ``jirafs.ticketfolder.TicketFolder`` representing
  the jira issue that this plugin is currently operating upon.
* ``self.get_configuration()``: Returns a dictionary of configuration settings for this
  plugin.
* ``self.get_metadata()``: Returns a dictionary containing metadata stored
  for this plugin.
* ``self.set_metadata(dict)``: Allows plugin to store metadata.  Data **must**
  be JSON serializable.


.. _macro_plugins:

Macro Plugin API
----------------

Macro plugins are special kinds of plugins that are instead subclasses of
either ``jirafs.plugin.BlockElementMacroPlugin`` or ``jirafs.plugin.VoidElementMacroPlugin``,
but same setuptools entrypoints apply as are described in :ref:`entry_points`.

Block Element Macros
~~~~~~~~~~~~~~~~~~~~

Block element macros are macros that wrap a body of text -- for example::

    {my-macro}
    Some content
    {my-macro}

Note that -- following JIRA's markup conventions, the macro both begins and ends
with the name of your macro.  Your macro class needs to have only one method --
``execute_macro`` which receives both the text content wrapped by the two
``{my-macro}`` markers, as well as any parameters (as keyword arguments).

.. note::
    
   See :ref:`macro_parameters` for more information about parameters.

Your ``execute_macro`` method is expected to return text that should be sent
to JIRA instead of your macro.

Void Element Macros
~~~~~~~~~~~~~~~~~~~

Void element macros and block element macros share a lot of similarities, except
that void element macros do not need to be closed; for example::

    {my-void-element-macro}

Your ``execute_macro`` method is expected to return text that should be sent
to JIRA instead of your macro.  Note that the method signature remains
identical to that of a block element macro, but instead of receiving
the content of the block, you will receive ``None``.

.. _macro_parameters:

Parameters
~~~~~~~~~~

Both block and void elements can receive any number of parameters; they're
specified following JIRA's conventions in which each parameter is separated
by a pipe, and the key and value (if specified) are separated by an equal sign;
for example the following void element has three parameters::

    {flag-image:country_code=US|size=300|alternate}

* ``country_code``: ``US``
* ``size``: ``300``
* ``alternate``: ``True``

.. note::

   All parameters -- except ``True`` in the third example above --
   are passed as strings, and ``True`` is only a default value for
   parameters that do not have a value specified.

Example Macro Plugin
~~~~~~~~~~~~~~~~~~~~

The following plugin isn't exactly useful, but it does demonstrate
the basic functionality of a plugin:

.. code-block:: python

    class Plugin(BlockElementMacroPlugin):
        COMPONENT_NAME = 'upper-cased'

        def execute_macro(self, data, prefix='', **kwargs):
            return prefix + data.upper()

When you enter the following text into a JIRA ticket field::

    {upper-cased:prefix=Hello, }
    my name is Adam.
    {upper-cased}

the following content will be sent to JIRA instead::

    Hello, MY NAME IS ADAM.

.. warning::

   Note that it's always a good idea to make sure your ``execute_macro``
   method has a final parameter of ``**kwargs``!  In future versions of
   Jirafs, we may add more keyword arguments that will be sent automatically.
