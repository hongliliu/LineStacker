from __future__ import division
import numpy as np
import sys
import LineStacker.tools.fit

#lightspeed in km/s
c=299792458


class Image():
    def __init__(   self,
                    spectrum=[],
                    amp=[],
                    velocities=[],
                    frequencies=[],
                    z=None,
                    fEmLine=False,
                    centerIndex=None,
                    centralVelocity=None,
                    centralFrequency=None,
                    weights=1,
                    name='',
                    fit=False,
                    velOrFreq='vel'):

        """
            Image class, each object is a spectrum to stack,
            containing all necessary information to be stacked
            they can consist simply of a the flux array,
            or flux and corresponding spectral values
            Parameters
            ---------
            coords
                A coordList object of all target coordinates.
            spectrum
                spectrum should be of the shape [N,2] or [2,N]\r
                where N is the number of spectral bins\r
                The second dimension being the flux\r
                and the first the spectral values
            amp
                instead of defining spectrum one can define only the amplitude (flux)
            velocities=[]
                in the case where amp is defined\r
                it is still possible to define the velocites
            frequencies=[]
                in the case where amp is defined\r
                it is still possible to define the frequencies
            z
                redshift, one of the possible way to define central frequency\r
                if using redshift fEmLine (emission frequency of the line) should also be input
            fEmLine
                emission frequency of the line, needed if redshift argument is used
            centerIndex
                channel index of the line center, an other possible way to define line center
            centralFrequency
                (observed) frequency of the line center, an other possible way to define line center
            centralVelocity
                observed velocity of the line center, an other possible way to define line center
            weights
                the weighting scheme to use\r
                can be set to '1/A' or 'sigma2'\r
                if sigma2 is used std of the entire spectra used UNLESS, fit is set to True, in which case the part around the line is excluded from stf calculation (central here means one FWHM on each side of the center of the line)\r
                user input can be used, float or list (or array)
            name
                name of the image, can allow easier identification
            fit
                if fit is set to true, the spectrum will be fitted with a gaussian\r
                to try and identify the line center (as well as amplitude if weight is set to 1/A)
            velOrFreq
                defining if spectral dimension is velocity or frequency
        """

        self.velOrFreq=velOrFreq
        self.name=name
        self.z=z
        self.fEmLine=fEmLine
        self.fit=fit
        self.centerIndex=centerIndex
        self.centralVelocity=centralVelocity
        self.centralFrequency=centralFrequency
        self.spectrum=spectrum
        self.fEmLine=fEmLine


        if amp==[]: #if amplitude is not defined its extracted from the spectrum
            if self.spectrum.shape[1]==2:
                self.amp=spectrum[:,1]
            elif self.spectrum.shape[0]==2:
                self.amp=spectrum[1,:]
            else:
                raise Exception('spectrum does not have the good shape, should be a 2 dimensional array [velocities, amplitudes]')
        else:
            self.amp=amp
        if self.velOrFreq=='vel': #velocity mode
            if velocities==[]:#if the velocities are not defined they are extracted from the spectrum
                if spectrum!=[]:
                    if self.spectrum.shape[1]==2:
                        self.velocities=self.spectrum[:,0]
                    elif self.spectrum.shape[0]==2:
                        self.velocities=self.spectrum[0,:]
                    else:
                        raise Exception('spectrum does not have the good shape, should be a 2 dimensional array [velocities, amplitudes]')
                    #self.velocities=spectrum[:,0]
                else:   #if the spectrum is not defined either (so if only the amplitude are),
                        #the velocities are defined as a range centered on zero, of size=len(amp) and binsize=1
                    self.velocities=np.arange(-int(len(self.amp)/2),int(round(len(self.amp)/2.)))
                self.velBin=self.velocities[1]-self.velocities[0] #velocity bin size
            else:
                self.velocities=velocities
                self.velBin=self.velocities[1]-self.velocities[0] #velocity bin size
        elif self.velOrFreq=='freq': #frequency mode
            if frequencies==[]: #if the frequencies are not defined they are extracted from the spectrum
                if spectrum!=[]:
                    if self.spectrum.shape[1]==2:
                        self.frequencies=self.spectrum[:,0]
                    elif self.spectrum.shape[0]==2:
                        self.frequencies=self.spectrum[0,:]
                    else:
                        raise Exception('spectrum does not have the good shape, should be a 2 dimensional array [velocities, amplitudes]')
                    #self.frequencies=spectrum[:,0]
                else: #if the spectrum is not defined either (so if only the amplitude are),
                        #the frequencies are defined as a range sarting from 0, of size=len(amp) and binsize=1
                   self.frequencies=np.arange(0,len(self.amp))
            else:
                self.frequencies=frequencies
                self.freqBin=self.frequencies[1]-self.frequencies[0] #frequency bin size

        if self.z!=None: #use z and rest emission frequency to find stack center
            if self.fEmLine==False:
                raise Exception('No emission frequency for spectra number '+str(i)+' ('+image.name+'), you need an emission frequency in frequency mode, alternativelly z=0 would raise this error')
            fObsLine=self.fEmLine/(1.+self.z)
            centerIndex=int(round((fObsLine-self.frequencies[0])/self.freqBin))
            self.centerIndex=centerIndex
        elif self.centralVelocity!=None:
            self.centerIndex=int(round((self.centralVelocity-self.velocities[0])/self.velBin))
        elif self.centralFrequency!=None:
            self.centerIndex=int(round((self.centralFrequency-self.frequencies[0])/self.freqBin))
        if fit:#if fit is on, line parametres are estimated using gaussian fitting
            try:
                LineStacker.tools.fit
            except NameError:
                import LineStacker.tools.fit
            #if 'LineStacker.tools.fit' not in sys.modules:
            #    print 'fit module not imported'
            #    import LineStacker.tools.fit
            else:
                print 'imported'
            if velOrFreq=='vel':
                import LineStacker.tools.fit
                self.gaussfit=LineStacker.tools.fit.GaussFit(     fctToFit=self.amp,
                                                    fullFreq=self.velocities,
                                                    returnInfos=True)
                self.velCenter=self.gaussfit[1][1]
                self.centerIndex=int(round((self.velCenter-self.velocities[0])/self.velBin))
            if velOrFreq=='freq':
                self.gaussfit=LineStacker.tools.fit.GaussFit(     fctToFit=self.amp,
                                                    fullFreq=self.frequencies,
                                                    returnInfos=True)
                self.velCenter=self.gaussfit[1][1]
                self.centerIndex=int(round((self.velCenter-self.frequencies[0])/self.freqBin))
            self.lineWidth=self.gaussfit[1][2]

        if weights=='1/A': #weights set to 1 over amplitude
            if fit==False: #/!\ if not fitted the amplitude is defined as maximum value /!\
                self.weights=1./max(self.amp)
            else:
                self.weights=1./self.gaussfit[1][0]
        elif weights=='sigma2': #weights set to 1 over sigma**2
            if fit:
                if velOrFreq=='vel':
                    lineWidthInBins=self.lineWidth/velBin
                else:
                    lineWidthInBins=self.lineWidth/freqBin
                leftLimSpectra=int(self.centerIndex-lineWidthInBins*2.35)
                rightLimSpectra=int(self.centerIndex+lineWidthInBins*2.35)
                toSTD=[]
                if rightLimSpectra<len(self.amp)-1:
                    toSTD.append(self.amp[rightLimSpectra:])
                if leftLimSpectra>0:
                    toSTD.append(self.amp[:leftLimSpectra])
                if toSTD==[]:
                    raise Exception('it seems your line is too large to use sigma2 weighting')
                self.weights=1./np.std(toSTD)**2
            else:
                self.weights=1./np.std(self.amp)**2 #calculating standard deviation of the ENTIRE spectrum
        else:
            self.weights=weights

    #functions to go from velocites to frequencies and vice versa, requieres rest emission frequency
    def velToFreq(vel,z, fEmLine):
        fObsLine=fEmLine/(1+z)
        return fObsLine*(vel/(vel+c))
    def freqToVel(freq,z, fEmLine):
        fObsLine=fEmLine/(1+z)
        deltaF=freq-fObsLine
        return c*((fObsLine/(fObsLine-deltaF))-1)


def Stack(  Images,
            chansStack='full',
            method='mean',
            center='lineCenterIndex',
            velOrFreq='vel'):

    """
        Main (one dimmensional) stacking function
        requieres list of Image objects
        Parameters
        ---------
        Images
            list of images, images have to objects of the Image class (LineStacker.OneD_Stacker.Image)
        chansStack
            number of channels to stack
            set to 'full' to stack all channels from all images
            user input (int) otherwise
        method
            stacking method, 'mean' and 'median' supported
        center
            method to find central frequency of the stack, possible values are
            "center", to stack all spectra center to center,
            'fit' to use gaussian fitting on the spectrum to determine line center
            'zero_vel' to stack on velocity=0 bin
            'lineCenterIndex' use the line center initiated with the image
            dirrectly defined by the user (int)
        velOrFreq
            'vel' or 'freq', frequency or velocity mode

    """

    for (i,image) in enumerate(Images):
        #if image.centerIndex==None:
        if center=='fit':
            #if image.fit==True:
            #    centerIndex=image.centerIndex
            #else: #if the image was not fitted when initiated
            if 'LineStacker.tools.fit' not in sys.modules:
                print 'fit module not imported'
                import LineStacker.tools.fit
            '''/!\
            '''
            import LineStacker.tools.fit
            if image.velocities!=[]:
                tempGaussfit=LineStacker.tools.fit.GaussFit(     fctToFit=image.amp,
                                                    fullFreq=image.velocities,
                                                    returnInfos=True)[1]
                tempVelCenter=tempGaussfit[1] #fit to determine center index
                image.centerIndex=int(round((tempVelCenter-image.velocities[0])/image.velBin))
            else:
                tempGaussfit=LineStacker.tools.fit.GaussFit(     fctToFit=image.amp,
                                                    returnInfos=True)[1]
                image.centerIndex=tempGaussfit[1]


        elif center=='zero_vel': #center on v=0km/s
            try:
                if type(image.velocities)!=list:
                    image.centerIndex=image.velocities.tolist().index(0.)
                else:
                    image.centerIndex=image.velocities.index(0.)
            except ValueError: #if the value 0 is not found, search closest
                centerIndex=-image.velocities[0]/image.velBin
                if centerIndex<0 or centerIndex>len(image.velocities):
                    raise Exception('zero velocity not found')
                image.centerIndex=centerIndex

        elif center=='center': #center on the center of the array
            centerIndex=int(len(image.amp)/2)
            image.centerIndex=centerIndex


        elif center=='lineCenterIndex':
            if image.centerIndex==None:
                raise Exception('center set to lineCenterIndex but no center index is found for line '+str(i))
            else:
                pass
        else: #user defined center
            image.centerIndex=center

    if chansStack=='full': #use all bins
        pass
    elif type(chansStack)==int: #need to shorten image size to fit user size, center on stack center (centerIndex)
        for (i, image) in enumerate(Images):
            newImageLeftLim=max(0, int(image.centerIndex-chansStack/2))
            newImageRightLim=min(len(Images[i].amp), int(image.centerIndex+chansStack/2))
            Images[i].amp=Images[i].amp[newImageLeftLim:newImageRightLim]
            if image.velocities!=[]:
                Images[i].velocities=Images[i].velocities[newImageLeftLim:newImageRightLim]
            if image.frequencies!=[]:
                Images[i].frequencies=Images[i].frequencies[newImageLeftLim:newImageRightLim]
    else:
        raise Exception("chansStack must be an int or 'full' for full spectra" )

    max_size=[int(max([image.centerIndex for image in Images])),
        int(max([len(image.velocities)-image.centerIndex for image in Images]))] #determine the size of the stack output
    toStack=np.zeros(( len(Images), max_size[0]+max_size[1])) #create an array, to be filled that will be stacked
    for index in range(-max_size[0],max_size[1]):
        for (i,image) in enumerate(Images):
            if 0<=image.centerIndex+index<len(image.amp): #add to stack only if stacked spectrum defined at this distance from center
                toStack[i][index+max_size[0]]=image.amp[image.centerIndex+index]
            else:
                toStack[i][index+max_size[0]]=np.NaN
    stacked=np.zeros(max_size[0]+max_size[1]) #initialize the actual stack output
    numberOfSourcePerStack=np.zeros(max_size[0]+max_size[1]) #initialize the number of sources stacked in every channel

    if method=='mean':
        for j in range(max_size[0]+max_size[1]):
            notEmptyPos=np.where( ([not(np.isnan(image[j])) for image in toStack]) )[0] #only stack sources that are not empty at this distance from stack center
            if notEmptyPos!=[]:
                if type(Images[0].weights)!=list and type(Images[0].weights)!=np.ndarray: #if weigths is just one value per spectrum
                    stacked[j]=np.average( ([ toStack[int(ll)][j] for ll in notEmptyPos]), weights=([Images[int(ll)].weights for ll in notEmptyPos]) )
                else: #if weigth is defined as an array/list (individually for each sectral channel)
                    stacked[j]=np.average( ([ toStack[int(ll)][j] for ll in notEmptyPos]), weights=([Images[int(ll)].weights[j-max_size[0]+Images[ll].centerIndex] for ll in notEmptyPos]) )
            numberOfSourcePerStack[j]=np.sum([1 for pos in notEmptyPos])

    if method=='median':
        for j in range(max_size[0]+max_size[1]):
            notEmptyPos=np.where( ([not(np.isnan(image[j])) for image in toStack]) )[0]
            if notEmptyPos!=[]:
                stacked[j]=np.median( ([ toStack[int(ll)][j] for ll in notEmptyPos]))
            numberOfSourcePerStack[j]=np.sum([1 for pos in notEmptyPos])

    return stacked, numberOfSourcePerStack
