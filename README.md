# What is this?

This is my configuration that I use across all of my projects for YouCompleteMe! I made it because generating .ycm_extra_conf.py files becomes a huge pain after a while. It follows pep8 styling guidelines because I don't work at Google (sorry Google friends ;).

# Features

It can handle providing autocompletion for different source files with completely different compile_commands.json at the same time. It will keep the compile_commands.json file for each file loaded in memory though, so be wary!

It also does not require writing Python .ycm_extra_conf.py files for projects that simply need a few changes to their flags. Instead, we use simple yaml files for instances where we need to change the final flags that get presented to YouCompleteMe. This file is called ycm_extra_conf.yml, and can be placed in or above the root directory of your project. An example configuration that I use for developing on the Linux kernel:

```yaml
flags:
  add:
    - "-Wno-address-of-packed-member"
  remove:
    - "-DCC_HAVE_ASM_GOTO"
```

It's likely more options for simple flag modifications will be added in the future.

# How to use?

Make sure you're using python3 to run YouCompleteMe. This project was written for the current era, we don't care about python2 support and neither should you.

Besides that, read the YCM manual!
