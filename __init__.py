def classFactory(iface):
    from .src.plugin import BlocksNetPlugin
    return BlocksNetPlugin(iface)