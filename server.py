from twisted.words import xmpproutertap as tap

opt = tap.Options()
opt.parseOptions([])
s = tap.makeService(opt)

