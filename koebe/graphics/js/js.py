# Blank python file so that the JavaScript code in this directory
# can be loaded using pkgutil.get_data("js.js", "p5viewer.js").decode("utf8")
#
# There must be a way to have pkgutil.get_data simply use the current module, 
# but I don't see it in the documentation (love you Python...) and passing both
# None and "" as the directory doesn't work so this is my quick and dirty 
# workaround. 
#
# Hopefully someone will fix this...