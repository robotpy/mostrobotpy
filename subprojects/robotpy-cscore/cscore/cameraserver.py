#*----------------------------------------------------------------------------*/
#* Copyright (c) FIRST 2016-2017. All Rights Reserved.                        */
#* Open Source Software - may be modified and shared by FRC teams. The code   */
#* must be accompanied by the FIRST BSD license file in the root directory of */
#* the project.                                                               */
#*----------------------------------------------------------------------------*/

# TODO: should this be distributed here, or with WPILib? My gut says here, 
# because it's useful here too.

import re
import threading

import cscore
from cscore import VideoEvent, VideoProperty, VideoSink, VideoSource
from networktables import NetworkTables

class VideoException(Exception):
    pass

class CameraServer:
    """Singleton class for creating and keeping camera servers.
    Also publishes camera information to NetworkTables.
    """
    
    kBasePort = 1181
    kPublishName = "/CameraPublisher"

    @classmethod
    def getInstance(cls):
        """Get the CameraServer instance."""
        try:
            return cls._server
        except AttributeError:
            cls._server = cls()
            return cls._server
    
    @staticmethod
    def _makeSourceValue(source):
        kind = CameraServerJNI.getSourceKind(source)
        if kind == cscore.kUsb:
            return "usb:" + CameraServerJNI.getUsbCameraPath(source)
        
        elif kind == cscore.kHttp:
            urls = CameraServerJNI.getHttpCameraUrls(source)
            if urls:
                return "ip:" + urls[0]
            else:
                return "ip:"
            
        elif kind == cscore.kCv:
            # FIXME: Should be "cv:", but LabVIEW dashboard requires "usb:".
            # https://github.com/wpilibsuite/allwpilib/issues/407
            return "usb:"
        
        else:
            return "unknown:"
    
    @staticmethod
    def _makeStreamValue(address, port):
        return "mjpg:http://%s:%s/?action=stream" % (address, port)
    
    def _getSourceTable(self, source):
        with self._mutex:
            return self._tables.get(source)
    
    def _getSinkStreamValues(self, sink):
        with self._mutex:
            # Ignore all but MjpegServer
            if VideoSink.getKindFromInt(CameraServerJNI.getSinkKind(sink)) != VideoSink.Kind.kMjpeg:
                return []
            
            # Get port
            port = CameraServerJNI.getMjpegServerPort(sink)
    
            # Generate values
            values = [] #new ArrayList<String>(self._addresses.length + 1)
            listenAddress = CameraServerJNI.getMjpegServerListenAddress(sink)
            if listenAddress:
                # If a listen address is specified, only use that
                values.add(CameraServer._makeStreamValue(listenAddress, port))
            else:
                # Otherwise generate for hostname and all interface addresses
                values.add(CameraServer._makeStreamValue(CameraServerJNI.getHostname() + ".local", port))
                for addr in self._addresses:
                    if addr == "127.0.0.1":
                        continue    # ignore localhost
                    
                    values.add(CameraServer._makeStreamValue(addr, port))
    
            return values
    
    def _getSourceStreamValues(self, source):
        with self._mutex:
            # Ignore all but HttpCamera
            if VideoSource.getKindFromInt(CameraServerJNI.getSourceKind(source)) != VideoSource.Kind.kHttp:
                return []
            
            # Generate values
            values = ['mjpg:%s' % v for v in CameraServerJNI.getHttpCameraUrls(source)]
            
            # Look to see if we have a passthrough server for this source
            for i in self._sinks.values():
                sink = i.getHandle()
                sinkSource = CameraServerJNI.getSinkSource(sink)
                if source == sinkSource \
                    and VideoSink.getKindFromInt(CameraServerJNI.getSinkKind(sink)) == VideoSink.Kind.kMjpeg:
                    # Add USB-only passthrough
                    port = CameraServerJNI.getMjpegServerPort(sink)
                    values.append(CameraServer._makeStreamValue("172.22.11.2", port))
                    break
            
            return values
    
    def _updateStreamValues(self):
        with self._mutex:
            # Over all the sinks...
            for i in self._sinks.values():
                sink = i.getHandle()
    
                # Get the source's subtable (if none exists, we're done)
                source = CameraServerJNI.getSinkSource(sink)
                if not source:
                    continue
                
                table = self._tables.get(source)
                if table is not None:
                    # Don't set stream values if this is a HttpCamera passthrough
                    if (VideoSource.getKindFromInt(CameraServerJNI.getSourceKind(source))
                            == VideoSource.Kind.kHttp):
                        continue
                    
                    # Set table value
                    values = self._getSinkStreamValues(sink)
                    if values.length:
                        table.putStringArray("streams", values)
            
            # Over all the sources...
            for i in self._sources.values():
                source = i.getHandle()
    
                # Get the source's subtable (if none exists, we're done)
                table = self._tables.get(source)
                if table is not None:
                    # Set table value
                    values = self._getSourceStreamValues(source)
                    if values.length > 0:
                        table.putStringArray("streams", values)
    
    _pixelFormats = {
        cscore.PixelFormat.kMJPEG: "MJPEG",
        cscore.PixelFormat.kYUYV: "YUYV",
        cscore.PixelFormat.kRGB565: "RGB565",
        cscore.PixelFormat.kBGR: "BGR",
        cscore.PixelFormat.kGray: "Gray",
    }
    
    @classmethod
    def _pixelFormatToString(cls, pixelFormat):
        return cls._pixelFormats.get(pixelFormat, "Unknown")
    
    _pixelFmtStrings = {
        "MJPEG": cscore.PixelFormat.kMJPEG,
        "mjpeg": cscore.PixelFormat.kMJPEG,
        "JPEG": cscore.PixelFormat.kMJPEG,
        "jpeg": cscore.PixelFormat.kMJPEG,
        
        "YUYV": cscore.PixelFormat.kYUYV,
        "yuyv": cscore.PixelFormat.kYUYV,
        
        "RGB565": cscore.PixelFormat.kRGB565,
        "rgb565": cscore.PixelFormat.kRGB565,
        
        "BGR": cscore.PixelFormat.kBGR,
        "bgr": cscore.PixelFormat.kBGR,
        
        "GRAY": cscore.PixelFormat.kGRAY,
        "Gray": cscore.PixelFormat.kGRAY,
        "gray": cscore.PixelFormat.kGRAY,
    }
        
    @classmethod
    def _pixelFormatFromString(cls, pixelFormatStr):
        return cls._pixelFmtStrings.get(pixelFormatStr, cscore.PixelFormat.kUnknown)
    
    
    _reMode = re.compile("(?<width>[0-9]+)\\s*x\\s*(?<height>[0-9]+)\\s+(?<format>.*?)\\s+"
                         "(?<fps>[0-9.]+)\\s*fps")

    @classmethod
    def _videoModeFromString(cls, modeStr):
        '''Construct a video mode from a string description.'''
        matcher = cls._reMode.match(modeStr)
        if not matcher:
            return cscore.VideoMode(cscore.PixelFormat.kUnknown, 0, 0, 0)
        
        pixelFormat = cls._pixelFormatFromString(matcher.group("format"))
        width = int(matcher.group("width"))
        height = int(matcher.group("height"))
        fps = int(float(matcher.group("fps")))
        return cscore.VideoMode(pixelFormat, width, height, fps)
    

    @classmethod
    def _videoModeToString(cls, mode):
        """/// Provide string description of video mode.
        /// The returned string is "{widthx{height:format:fpsfps".
        """
        return (mode.width + "x" + mode.height + " " + cls._pixelFormatToString(mode.pixelFormat)
                + " " + mode.fps + " fps")
    
    @classmethod
    def _getSourceModeValues(cls, sourceHandle):
        modes = CameraServerJNI.enumerateSourceVideoModes(sourceHandle)
        return [cls._videoModeToString(mode) for mode in modes]

    @staticmethod
    def _putSourcePropertyValue(table, event, isNew):
        if (event.name.startsWith("raw_")):
            name = "RawProperty/" + event.name[4:]
            infoName = "RawPropertyInfo/" + event.name[4:]
        else:
            name = "Property/" + event.name
            infoName = "PropertyInfo/" + event.name
        
        propertyKind = event.propertyKind

        if propertyKind == cscore.Kind.kBoolean:
            if isNew:
                table.setDefaultBoolean(name, event.value != 0)
            else:
                table.putBoolean(name, event.value != 0)
                
        elif propertyKind in [cscore.Kind.kInteger, cscore.Kind.kEnum]:
            if isNew:
                table.setDefaultNumber(name, event.value)
                table.putNumber(infoName + "/min",
                        CameraServerJNI.getPropertyMin(event.propertyHandle))
                table.putNumber(infoName + "/max",
                        CameraServerJNI.getPropertyMax(event.propertyHandle))
                table.putNumber(infoName + "/step",
                        CameraServerJNI.getPropertyStep(event.propertyHandle))
                table.putNumber(infoName + "/default",
                        CameraServerJNI.getPropertyDefault(event.propertyHandle))
            else:
                table.putNumber(name, event.value)
            
        elif propertyKind == cscore.Kind.kString:
            if isNew:
                table.setDefaultString(name, event.valueStr)
            else:
                table.putString(name, event.valueStr)
    
    def __init__(self):
        self._mutex = threading.RLock()
        self._sources = {}  # type: Dict[str, VideoSource]
        self._sinks = {}  # type: Dict[str, VideoSink]
        self._tables = {}  # type: Dict[int, networktables.NetworkTable]
        self._publishTable = NetworkTables.getTable(self.kPublishName)
        self._nextPort = self.kBasePort
        self._addresses = []

        # We publish sources to NetworkTables using the following structure:
        # "/CameraPublisher/{Source.Name/" - root
        # - "source" (string): Descriptive, prefixed with type (e.g. "usb:0")
        # - "streams" (string array): URLs that can be used to stream data
        # - "description" (string): Description of the source
        # - "connected" (boolean): Whether source is connected
        # - "mode" (string): Current video mode
        # - "modes" (string array): Available video modes
        # - "Property/{Property" - Property values
        # - "PropertyInfo/{Property" - Property supporting information

        # Listener for video events
        self._videoListener = cscore.VideoListener(self.onVideoEvent, 0x4fff, True)

        # Listener for NetworkTable events
        self._tableListener = NetworkTablesJNI.addEntryListener(self.kPublishName + "/", self.onTableChange, ITable.NOTIFY_IMMEDIATE | ITable.NOTIFY_UPDATE)

    def onVideoEvent(self, event):
        if event.kind == VideoEvent.Kind.kSourceCreated:
            # Create subtable for the camera
            table = self._publishTable.getSubTable(event.name)
            with self._mutex:
                self._tables.put(event.sourceHandle, table)

            table.putString("source", CameraServer._makeSourceValue(event.sourceHandle))
            table.putString("description",
                    CameraServerJNI.getSourceDescription(event.sourceHandle))
            table.putBoolean("connected", CameraServerJNI.isSourceConnected(event.sourceHandle))
            table.putStringArray("streams", self._getSourceStreamValues(event.sourceHandle))
            mode = CameraServerJNI.getSourceVideoMode(event.sourceHandle)  # type: cscore.VideoMode
            table.setDefaultString("mode", CameraServer._videoModeToString(mode))
            table.putStringArray("modes", CameraServer._getSourceModeValues(event.sourceHandle))

        elif event.kind == VideoEvent.Kind.kSourceDestroyed:
            table = self._getSourceTable(event.sourceHandle)
            if table is not None:
                table.putString("source", "")
                table.putStringArray("streams", [])
                table.putStringArray("modes", [])

        elif event.kind == VideoEvent.Kind.kSourceConnected:
            table = self._getSourceTable(event.sourceHandle)
            if table is not None:
                # update the description too (as it may have changed)
                table.putString("description",
                        CameraServerJNI.getSourceDescription(event.sourceHandle))
                table.putBoolean("connected", True)

        elif event.kind == VideoEvent.Kind.kSourceDisconnected:
            table = self._getSourceTable(event.sourceHandle)
            if table is not None:
                table.putBoolean("connected", False)

        elif event.kind == VideoEvent.Kind.kSourceVideoModesUpdated:
            table = self._getSourceTable(event.sourceHandle)
            if table is not None:
                table.putStringArray("modes", CameraServer._getSourceModeValues(event.sourceHandle))

        elif event.kind == VideoEvent.Kind.kSourceVideoModeChanged:
            table = self._getSourceTable(event.sourceHandle)
            if table is not None:
                table.putString("mode", CameraServer._videoModeToString(event.mode))

        elif event.kind == VideoEvent.Kind.kSourcePropertyCreated:
            table = self._getSourceTable(event.sourceHandle)
            if table is not None:
                CameraServer._putSourcePropertyValue(table, event, True)

        elif event.kind == VideoEvent.Kind.kSourcePropertyValueUpdated:
            table = self._getSourceTable(event.sourceHandle)
            if table is not None:
                CameraServer._putSourcePropertyValue(table, event, False)

        elif event.kind == VideoEvent.Kind.kSourcePropertyChoicesUpdated:
            table = self._getSourceTable(event.sourceHandle)
            if table is not None:
                choices = CameraServerJNI.getEnumPropertyChoices(event.propertyHandle)  # type: List[str]
                table.putStringArray("PropertyInfo/" + event.name + "/choices", choices)

        elif event.kind in (VideoEvent.Kind.kSinkSourceChanged, VideoEvent.Kind.kSinkCreated, VideoEvent.Kind.kSinkDestroyed):
            self._updateStreamValues()

        elif event.kind == VideoEvent.Kind.kNetworkInterfacesChanged:
            self._addresses = CameraServerJNI.getNetworkInterfaces()

    def onTableChange(self, uid, key, value, flags):
        relativeKey = key[len(self.kPublishName) + 1:]  # type: str

        # get source (sourceName/...)
        subKeyIndex = relativeKey.find('/')
        if subKeyIndex == -1:
            return

        sourceName = relativeKey[0:subKeyIndex]
        source = self._sources.get(sourceName)  # type: VideoSource
        if source is None:
            return

        # get subkey
        relativeKey = relativeKey[subKeyIndex + 1:]

        # handle standard names
        if relativeKey == "mode":
            mode = CameraServer._videoModeFromString(value)  # type: cscore.VideoMode
            if mode.pixelFormat == cscore.PixelFormat.kUnknown or not source.setVideoMode(mode):
                # reset to current mode
                NetworkTablesJNI.putString(key, CameraServer._videoModeToString(source.getVideoMode()))
            return
        elif relativeKey.startswith("Property/"):
            propName = relativeKey[9:]
        elif relativeKey.startswith("RawProperty/"):
            propName = "raw_" + relativeKey[12:]
        else:
            return    # ignore

        # everything else is a property
        property = source.getProperty(propName)  # type: VideoProperty
        if not property.isValid():
            return
        elif property.isBoolean():
            property.set(1 if value.booleanValue() else 0)
        elif property.isInteger() or property.isEnum():
            property.set(value.intValue())
        elif property.isString():
            property.setString(value)

    def startAutomaticCapture(self):
        """Start automatically capturing images to send to the dashboard.
        
        <p>You should call this method to see a camera feed on the dashboard.
        If you also want to perform vision processing on the roboRIO, use
        getVideo() to get access to the camera images.
        
        <p>This overload calls:@link #startAutomaticCapture(int)with device 0,
        creating a camera named "USB Camera 0".
        """
        return self.startAutomaticCapture(0)
    

    def startAutomaticCapture(self, dev):
        """Start automatically capturing images to send to the dashboard.
        
        <p>This overload calls:@link #startAutomaticCapture(String, int)with
        a name of "USB Camera:dev".
        
        :param dev: The device number of the camera interface
        :type dev: int
        """
        camera = cscore.UsbCamera("USB Camera %d" % dev, dev)
        self.startAutomaticCapture(camera)
        return camera
    

    def startAutomaticCapture(self, name, dev):
        """Start automatically capturing images to send to the dashboard.
        
        :param name: The name to give the camera
        :param dev: The device number of the camera interface
        """
        camera = cscore.UsbCamera(name, dev)
        self.startAutomaticCapture(camera)
        return camera
    

    def startAutomaticCapture(self, name, path):
        """Start automatically capturing images to send to the dashboard.
        
        :param name: The name to give the camera
        :param path: The device path (e.g. "/dev/video0") of the camera
        """
        camera = cscore.UsbCamera(name, path)
        self.startAutomaticCapture(camera)
        return camera
    

    def startAutomaticCapture(self, camera):
        """Start automatically capturing images to send to the dashboard from
        an existing camera.
        
        :param camera: Camera
        """
        self.addCamera(camera)
        server = self.addServer("serve_" + camera.getName())
        server.setSource(camera)
    

    def addAxisCamera(self, host):
        """Adds an Axis IP camera.
        
        <p>This overload calls:@link #addAxisCamera(String, String)with
        name "Axis Camera".
        
        :param host: Camera host IP or DNS name (e.g. "10.x.y.11")
        """
        return self.addAxisCamera("Axis Camera", host)
    

    def addAxisCamera(self, hosts):
        """Adds an Axis IP camera.
        
        <p>This overload calls:@link #addAxisCamera(String, String[])with
        name "Axis Camera".
        
        :param hosts: Array of Camera host IPs/DNS names
        """
        return self.addAxisCamera("Axis Camera", hosts)
    

    def addAxisCamera(self, name, host):
        """Adds an Axis IP camera.
        
        :param name: The name to give the camera
        :param host: Camera host IP or DNS name (e.g. "10.x.y.11")
        """
        camera = cscore.AxisCamera(name, host)
        # Create a passthrough MJPEG server for USB access
        self.startAutomaticCapture(camera)
        return camera
    

    def addAxisCamera(self, name, hosts):
        """Adds an Axis IP camera.
        
        :param name: The name to give the camera
        :param hosts: Array of Camera host IPs/DNS names
        """
        camera = cscore.AxisCamera(name, hosts)
        # Create a passthrough MJPEG server for USB access
        self.startAutomaticCapture(camera)
        return camera
    

    def getVideo(self):
        """Get OpenCV access to the primary camera feed.    This allows you to
        get images from the camera for image processing on the roboRIO.
        
        This is only valid to call after a camera feed has been added
        with :meth:`startAutomaticCapture` or :meth:`addServer`.
        """
        with self._mutex:
            if self._primarySourceName is None:
                raise VideoException("no camera available")
            
            source = self._sources.get(self._primarySourceName)
        
        if source is None:
            raise VideoException("no camera available")
        
        return self.getVideo(source)
    

    def getVideo(self, camera):
        """Get OpenCV access to the specified camera.    This allows you to get
        images from the camera for image processing on the roboRIO.
        
        :param camera: Camera (e.g. as returned by startAutomaticCapture).
        """
        name = "opencv_" + camera.getName()

        with self._mutex:
            sink = self._sinks.get(name)  # type: cscore.VideoSink
            if sink is not None:
                kind = sink.getKind()
                if kind != cscore.VideoSink.Kind.kCv:
                    raise VideoException("expected OpenCV sink, but got " + kind)
                
                return sink
        
        newsink = cscore.CvSink(name)
        newsink.setSource(camera)
        self.addServer(newsink)
        return newsink
    

    def getVideo(self, name):
        """Get OpenCV access to the specified camera.    This allows you to get
        images from the camera for image processing on the roboRIO.
        
        :param name: Camera name
        """
        with self._mutex:
            source = self._sources.get(name)
            if source is None:
                raise VideoException("could not find camera " + name)
        
        return self.getVideo(source)
    
    def putVideo(self, name, width, height):
        """Create a MJPEG stream with OpenCV input. This can be called to pass custom
        annotated images to the dashboard.
        
        :param name: Name to give the stream
        :param width: Width of the image being sent
        :param height: Height of the image being sent
        """
        source = cscore.CvSource(name, cscore.VideoMode.PixelFormat.kMJPEG, width, height, 30)
        self.startAutomaticCapture(source)
        return source
    
    def addServer(self, name):
        """Adds a MJPEG server at the next available port.
        
        :param name: Server name
        """
        with self._mutex:
            port = self._nextPort
            self._nextPort += 1
        
        return self.addServer(name, port)

    def addServer(self, name, port):
        """Adds a MJPEG server.
        
        :param name: Server name
        """
        server = cscore.MjpegServer(name, port)
        self.addServer(server)
        return server
    
    def addServer(self, server):
        """Adds an already created server.
        
        :param server: Server
        """
        with self._mutex:
            self._sinks.put(server.getName(), server)
        
    def removeServer(self, name):
        """Removes a server by name.
        
        :param name: Server name
        """
        with self._mutex:
            self._sinks.pop(name, None)
    
    def addCamera(self, camera):
        """Adds an already created camera.
        
        :param camera: Camera
        """
        name = camera.getName()
        with self._mutex:
            if self._primarySourceName is None:
                self._primarySourceName = name
            
            self._sources.put(name, camera)
    
    def removeCamera(self, name):
        """Removes a camera by name.
        
        :param name: Camera name
        """
        with self._mutex:
            self._sources.pop(name, None)
