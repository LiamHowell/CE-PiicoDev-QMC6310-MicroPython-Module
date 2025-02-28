_E=True
_D=None
_C=False
_B='y'
_A='x'
import math
from PiicoDev_Unified import *
compat_str='\nUnified PiicoDev library out of date.  Get the latest module: https://piico.dev/unified \n'
_I2C_ADDRESS=28
_ADDRESS_XOUT=1
_ADDRESS_YOUT=3
_ADDRESS_ZOUT=5
_ADDRESS_STATUS=9
_ADDRESS_CONTROL1=10
_ADDRESS_CONTROL2=11
_BIT_MODE=0
_BIT_ODR=2
_BIT_OSR1=4
_BIT_OSR2=6
_BIT_RANGE=2
def _readBit(x,n):return x&1<<n!=0
def _setBit(x,n):return x|1<<n
def _clearBit(x,n):return x&~(1<<n)
def _writeBit(x,n,b):
	if b==0:return _clearBit(x,n)
	else:return _setBit(x,n)
def _writeCrumb(x,n,c):x=_writeBit(x,n,_readBit(c,0));return _writeBit(x,n+1,_readBit(c,1))
class PiicoDev_QMC6310:
	range_gauss={3000:0.001,1200:0.0004,800:0.00026666667,200:6.6666667e-05};range_microtesla={3000:0.1,1200:0.04,800:0.026666667,200:0.0066666667}
	def __init__(self,bus=_D,freq=_D,sda=_D,scl=_D,addr=_I2C_ADDRESS,odr=3,osr1=0,osr2=3,range=3000,calibrationFile='calibration.cal'):
		try:
			if compat_ind>=1:0
			else:print(compat_str)
		except:print(compat_str)
		self.i2c=create_unified_i2c(bus=bus,freq=freq,sda=sda,scl=scl);self.addr=addr;self.odr=odr;self.calibrationFile=calibrationFile;self._CR1=0;self._CR2=0
		try:self._setMode(1);self.setOutputDataRate(odr);self.setOverSamplingRatio(osr1);self.setOverSamplingRate(osr2);self.setRange(range)
		except Exception as e:print(i2c_err_str.format(self.addr));raise e
		self.x_offset=0;self.y_offset=0;self.z_offset=0;self.declination=0;self.data={};self._dataValid=_C;self.loadCalibration();sleep_ms(5)
	def _setMode(self,mode):self._CR1=_writeCrumb(self._CR1,_BIT_MODE,mode);self.i2c.writeto_mem(self.addr,_ADDRESS_CONTROL1,bytes([self._CR1]))
	def setOutputDataRate(self,odr):self._CR1=_writeCrumb(self._CR1,_BIT_ODR,odr);self.i2c.writeto_mem(self.addr,_ADDRESS_CONTROL1,bytes([self._CR1]))
	def setOverSamplingRatio(self,osr1):self._CR1=_writeCrumb(self._CR1,_BIT_OSR1,osr1);self.i2c.writeto_mem(self.addr,_ADDRESS_CONTROL1,bytes([self._CR1]))
	def setOverSamplingRate(self,osr2):self._CR1=_writeCrumb(self._CR1,_BIT_OSR2,osr2);self.i2c.writeto_mem(self.addr,_ADDRESS_CONTROL1,bytes([self._CR1]))
	def setRange(self,range):assert range in[3000,1200,800,200],'range must be 200,800,1200,3000 (uTesla)';r={3000:0,1200:1,800:2,200:3};self.sensitivity=self.range_microtesla[range];self._CR2=_writeCrumb(self._CR2,_BIT_RANGE,r[range]);self.i2c.writeto_mem(self.addr,_ADDRESS_CONTROL2,bytes([self._CR2]))
	def _convertAngleToPositive(self,angle):
		if angle>=360.0:angle=angle-360.0
		if angle<0:angle=angle+360.0
		return angle
	def _getControlRegisters(self):return self.i2c.readfrom_mem(self.addr,_ADDRESS_CONTROL1,2)
	def _getStatusReady(self,status):return _readBit(status,0)
	def _getStatusOverflow(self,status):return _readBit(status,1)
	def read(self,raw=_C):
		B='little';A='NaN';self._dataValid=_C;NaN={_A:float(A),_B:float(A),'z':float(A)}
		try:status=int.from_bytes(self.i2c.readfrom_mem(self.addr,_ADDRESS_STATUS,1),'big')
		except:print(i2c_err_str.format(self.addr));self.sample=NaN;return NaN
		if self._getStatusReady(status)is _E:
			try:x=int.from_bytes(self.i2c.readfrom_mem(self.addr,_ADDRESS_XOUT,2),B);y=int.from_bytes(self.i2c.readfrom_mem(self.addr,_ADDRESS_YOUT,2),B);z=int.from_bytes(self.i2c.readfrom_mem(self.addr,_ADDRESS_ZOUT,2),B)
			except:print(i2c_err_str.format(self.addr));self.sample=NaN;return self.sample
			if self._getStatusOverflow(status)is _E:return NaN
			if x>=32768:x=-(65535-x+1)
			x=x-self.x_offset
			if y>=32768:y=-(65535-y+1)
			y=y-self.y_offset
			if z>=32768:z=-(65535-z+1)
			z=z-self.z_offset
			if raw is _C:x*=self.sensitivity;y*=self.sensitivity;z*=self.sensitivity
			self.sample={_A:x,_B:y,'z':z};self._dataValid=_E;return self.sample
		else:print('Not Ready');self.sample=NaN;return self.sample
	def dataValid(self):return self._dataValid
	def readPolar(self):cartesian=self.read();angle=math.atan2(cartesian[_A],cartesian[_B])/math.pi*180.0+self.declination;angle=self._convertAngleToPositive(angle);magnitude=math.sqrt(cartesian[_A]*cartesian[_A]+cartesian[_B]*cartesian[_B]+cartesian['z']*cartesian['z']);return{'polar':angle,'Gauss':magnitude*100,'uT':magnitude}
	def readMagnitude(self):return self.readPolar()['uT']
	def readHeading(self):return self.readPolar()['polar']
	def setDeclination(self,dec):self.declination=dec
	def calibrate(self,enable_logging=_C):
		try:self.setOutputDataRate(3)
		except Exception as e:print(i2c_err_str.format(self.addr));raise e
		x_min=65535;x_max=-65535;y_min=65535;y_max=-65535;z_min=65535;z_max=-65535;log='';print('*** Calibrating.\n    Slowly rotate your sensor until the bar is full');print('[          ]',end='');range=1000;i=0;x=0;y=0;z=0;a=0.5
		while i<range:
			i+=1;sleep_ms(5);d=self.read(raw=_E);x=a*d[_A]+(1-a)*x;y=a*d[_B]+(1-a)*y;z=a*d['z']+(1-a)*z
			if x<x_min:x_min=x;i=0
			if x>x_max:x_max=x;i=0
			if y<y_min:y_min=y;i=0
			if y>y_max:y_max=y;i=0
			if z<z_min:z_min=z;i=0
			if z>z_max:z_max=z;i=0
			j=round(10*i/range);print('\r['+int(j)*'*'+int(10-j)*' '+']',end='')
			if enable_logging:log=log+(str(cartesian[_A])+','+str(cartesian[_B])+','+str(cartesian['z'])+'\n')
		self.setOutputDataRate(self.odr);self.x_offset=(x_max+x_min)/2;self.y_offset=(y_max+y_min)/2;self.z_offset=(z_max+z_min)/2;f=open(self.calibrationFile,'w');f.write('x_min:\n'+str(x_min)+'\nx_max:\n'+str(x_max)+'\ny_min:\n'+str(y_min)+'\ny_max:\n'+str(y_max)+'\nz_min\n'+str(z_min)+'\nz_max:\n'+str(z_max)+'\nx_offset:\n');f.write(str(self.x_offset)+'\ny_offset:\n'+str(self.y_offset)+'\nz_offset:\n'+str(self.z_offset));f.close()
		if enable_logging:flog=open('calibration.log','w');flog.write(log);flog.close
	def loadCalibration(self):
		try:
			f=open(self.calibrationFile,'r')
			for i in range(13):f.readline()
			self.x_offset=float(f.readline());f.readline();self.y_offset=float(f.readline());f.readline();self.z_offset=float(f.readline());sleep_ms(5)
		except:print("No calibration file found. Run 'calibrate()' for best results.  Visit https://piico.dev/p15 for more info.");sleep_ms(1000)