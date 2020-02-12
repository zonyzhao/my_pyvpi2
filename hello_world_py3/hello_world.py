import pyvpi
import pyvpi_cons as cons

def test_systfdata():
    """
    """
    def calltf(self):
        print(self.tfname+' zony')
    systfdata = pyvpi.SysTfData()
    systfdata.tfname = "$hello_world"
    systfdata = pyvpi.SysTfData(tfname = "$hello_world")
    systfdata.calltf = calltf
    pyvpi.registerSysTf(systfdata)

if __name__ == '__main__':
    test_systfdata()
