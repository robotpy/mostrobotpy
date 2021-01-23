
#include <pybind11/pybind11.h>
#include <pybind11/functional.h>
#include <pybind11/operators.h>
#include <pybind11/stl.h>
namespace py = pybind11;

#include "cscore_oo.h"
#include "cscore_cv.h"
using namespace cs;

#include <opencv2/opencv.hpp>

#include "ndarray_converter.h"
#include "wpiutil_converters.hpp"


// Use this to release the gil
// -> Prefer to not use this for short inline getters
typedef py::call_guard<py::gil_scoped_release> release_gil;



// Wrapper for VideoListener to prevent crashes on shutdown
class VideoListenerWrapper : public VideoListener {
public:
    VideoListenerWrapper(std::function<void(const VideoEvent&)> callback, int eventMask, bool immediateNotify) :
        VideoListener(callback, eventMask, immediateNotify),
        m_callback(callback)
    {}

    virtual ~VideoListenerWrapper() {}

private:
    // need a reference to this callback otherwise cscore crashes on exit
    std::function<void(const VideoEvent&)> m_callback;
};


PYBIND11_MODULE(_cscore, m) {

    NDArrayConverter::init_numpy();

    static int unused; // the capsule needs something to reference
    py::capsule cleanup(&unused, [](void *) {
        // don't release gil until after calling this
        SetDefaultLogger(20 /* WPI_LOG_INFO */);
        
        // but this MUST release the gil, or deadlock may occur
        py::gil_scoped_release __release;
        CS_Shutdown();
    });
    m.add_object("_cleanup", cleanup);
    
    // cscore_cpp.h
    
    py::class_<UsbCameraInfo> usbcamerainfo(m, "UsbCameraInfo");
    usbcamerainfo.doc() = "USB camera information";
    usbcamerainfo
      .def_readwrite("dev", &UsbCameraInfo::dev)
      .def_readwrite("path", &UsbCameraInfo::path)
      .def_readwrite("name", &UsbCameraInfo::name)
      .def_readwrite("otherPaths", &UsbCameraInfo::otherPaths)
      .def_readwrite("vendorId", &UsbCameraInfo::vendorId)
      .def_readwrite("productId", &UsbCameraInfo::productId)
      .def("__repr__", [](UsbCameraInfo &__inst){
         return std::string("<UsbCameraInfo dev=") + std::to_string(__inst.dev) + " path=" + __inst.path + " name=" + __inst.name + ">";
       });
    
    py::class_<CS_VideoMode> cs_videomode(m, "_CS_VideoMode");
    
    py::class_<VideoMode, CS_VideoMode> videomode(m, "VideoMode");
    videomode.doc() = "Video mode";
    videomode
      .def(py::init<cs::VideoMode::PixelFormat, int, int, int>(),
           py::arg("pixelFormat"), py::arg("width"), py::arg("height"), py::arg("fps"))
      .def_property("pixelFormat",
            [](VideoMode &__inst) { return (cs::VideoMode::PixelFormat)__inst.pixelFormat; },
            [](VideoMode &__inst, cs::VideoMode::PixelFormat v) { __inst.pixelFormat = v; })
      .def_readwrite("width", &VideoMode::width)
      .def_readwrite("height", &VideoMode::height)
      .def_readwrite("fps", &VideoMode::fps);
      
    
    py::enum_<VideoMode::PixelFormat>(videomode, "PixelFormat")
      .value("kUnknown", VideoMode::PixelFormat::kUnknown)
      .value("kMJPEG", VideoMode::PixelFormat::kMJPEG)
      .value("kYUYV", VideoMode::PixelFormat::kYUYV)
      .value("kRGB565", VideoMode::PixelFormat::kRGB565)
      .value("kBGR", VideoMode::PixelFormat::kBGR)
      .value("kGray", VideoMode::PixelFormat::kGray);
    
    #define def_status_fn(n, N, T, ...) def(n, [](T t) { \
        py::gil_scoped_release __r; \
        CS_Status s = 0; \
        return N(t, &s); \
    }, __VA_ARGS__)
    
    m.def("getNetworkInterfaces", &GetNetworkInterfaces, release_gil())
     .def_status_fn("getHttpCameraUrls", GetHttpCameraUrls, CS_Source, py::arg("source"))
     .def_status_fn("getUsbCameraPath", GetUsbCameraPath, CS_Source, py::arg("source"))
     .def("getTelemetryElapsedTime", &GetTelemetryElapsedTime, release_gil())
     .def("setTelemetryPeriod", &SetTelemetryPeriod, release_gil(),
          py::arg("seconds"))
     .def("setLogger", &SetLogger, py::arg("func"), py::arg("min_level"));

    // cscore_oo.h

    py::class_<VideoProperty> videoproperty(m, "VideoProperty");
    videoproperty.doc() = "A source or sink property.";
    videoproperty
      .def("getName", &VideoProperty::GetName, release_gil())
      .def("getKind", &VideoProperty::GetKind)
      .def("isBoolean", &VideoProperty::IsBoolean)
      .def("isInteger", &VideoProperty::IsInteger)
      .def("isString", &VideoProperty::IsString)
      .def("isEnum", &VideoProperty::IsEnum)
      .def("get", &VideoProperty::Get, release_gil())
      .def("set", &VideoProperty::Set, py::arg("value"), release_gil())
      .def("getMin", &VideoProperty::GetMin, release_gil())
      .def("getMax", &VideoProperty::GetMax, release_gil())
      .def("getStep", &VideoProperty::GetStep, release_gil())
      .def("getDefault", &VideoProperty::GetDefault, release_gil())
      .def("getString", (std::string (VideoProperty::*)() const)&VideoProperty::GetString, release_gil())
      /*.def("GetString", [](VideoProperty &__inst) {
        wpi::SmallVectorImpl<char> buf;
        auto __ret = __inst.GetString(buf);
        return std::make_tuple(__ret, buf);
      })*/
      .def("setString", &VideoProperty::SetString, py::arg("value"), release_gil())
      .def("getChoices", &VideoProperty::GetChoices, release_gil())
      .def("getLastStatus", &VideoProperty::GetLastStatus);
    
    py::enum_<VideoProperty::Kind>(videoproperty, "Kind")
      .value("kNone", VideoProperty::Kind::kNone)
      .value("kBoolean", VideoProperty::Kind::kBoolean)
      .value("kInteger", VideoProperty::Kind::kInteger)
      .value("kString", VideoProperty::Kind::kString)
      .value("kEnum", VideoProperty::Kind::kEnum);
    
    py::class_<VideoSource> videosource(m, "VideoSource");
    videosource.doc() = "A source for video that provides a sequence of frames.";
    videosource
      .def(py::init<cs::VideoSource>(), py::arg("source"))
      .def("getHandle", &VideoSource::GetHandle)
      .def(py::self == py::self)
      .def(py::self != py::self)
      .def("getKind", &VideoSource::GetKind, release_gil(),
          "Get the kind of the source")
      .def("getName", &VideoSource::GetName, release_gil(),
          "Get the name of the source. The name is an arbitrary identifier " 
          "provided when the source is created, and should be unique.")
      .def("getDescription", &VideoSource::GetDescription, release_gil(),
          "Get the source description.  This is source-kind specific.")
      .def("getLastFrameTime", &VideoSource::GetLastFrameTime, release_gil(),
          "Get the last time a frame was captured.")
      .def("setConnectionStrategy", &VideoSource::SetConnectionStrategy, py::arg("strategy"), release_gil(),
          "Set the connection strategy.  By default, the source will automatically "
          "connect or disconnect based on whether any sinks are connected.\n\n"
          ":param strategy: connection strategy (see ConnectionStrategy)")
      .def("isConnected", &VideoSource::IsConnected, release_gil(),
          "Is the source currently connected to whatever is providing the images?")
      .def("getProperty", &VideoSource::GetProperty, py::arg("name"), release_gil(),
          "Get a property.\n\n"
          ":param name: Property name\n"
          ":returns: Property contents (VideoSource.Kind.kNone if no property with the given name exists)")
      .def("enumerateProperties", &VideoSource::EnumerateProperties, release_gil(), "Enumerate all properties of this source")
      .def("getVideoMode", &VideoSource::GetVideoMode, release_gil(), "Get the current video mode.")
      .def("setVideoMode", [](VideoSource &__inst, VideoMode mode) {
        py::gil_scoped_release __release;
        return __inst.SetVideoMode(mode);
    }, py::arg("mode"),
        "Set the video mode.\n\n"
        ":param mode: Video mode")
      .def("setVideoMode", [](VideoSource &__inst, VideoMode::PixelFormat pixelFormat, int width, int height, int fps) {
        py::gil_scoped_release __release;
        return __inst.SetVideoMode(pixelFormat, width, height, fps);
      }, py::arg("pixelFormat"), py::arg("width"), py::arg("height"), py::arg("fps"),
          "Set the video mode.\n\n"
          ":param pixelFormat: desired pixel format\n"
          ":param width: desired width\n"
          ":param height: desired height\n"
          ":param fps: desired FPS\n"
          ":returns: True if set successfully")
      .def("setPixelFormat", &VideoSource::SetPixelFormat, py::arg("pixelFormat"), release_gil(),
          "Set the pixel format.\n\n"
          ":param pixelFormat: desired pixel format\n"
          ":returns: True if set successfully")
      .def("setResolution", &VideoSource::SetResolution, py::arg("width"), py::arg("height"), release_gil(),
          "Set the resolution.\n\n"
          ":param width: desired width\n"
          ":param height: desired height\n"
          ":returns: True if set successfully")
      .def("setFPS", &VideoSource::SetFPS, py::arg("fps"), release_gil(),
          "Set the frames per second (FPS).\n\n"
          ":param fps: desired FPS\n"
          ":returns: True if set successfully")
      .def("setConfigJson", [](VideoSource &__inst, wpi::StringRef config) {
        py::gil_scoped_release __release;
        return __inst.SetConfigJson(config);
      }, py::arg("config"),
        "Set video mode and properties from a JSON configuration string.\n\n"
        ":param config: Configuration\n"
        ":returns: True if set successfully")
      .def("getConfigJson", &VideoSource::GetConfigJson, release_gil(),
           "Get a JSON configuration string.\n\n"
           ":returns: JSON string")
      .def("getActualFPS", &VideoSource::GetActualFPS, release_gil(),
           "Get the actual FPS.\n\n"
           ":func:`.setTelemetryPeriod` must be called for this to be valid.\n\n"
           ":returns: Actual FPS averaged over the telemetry period.")
      .def("getActualDataRate", &VideoSource::GetActualDataRate, release_gil(),
           "Get the data rate (in bytes per second).\n\n"
           ":func:`.setTelemetryPeriod` must be called for this to be valid.\n\n"
           ":returns: Data rate averaged over the telemetry period.")
      .def("enumerateVideoModes", &VideoSource::EnumerateVideoModes, release_gil(),
          "Enumerate all known video modes for this source.")
      .def("getLastStatus", &VideoSource::GetLastStatus)
      .def("enumerateSinks", &VideoSource::EnumerateSinks, release_gil(),
          "Enumerate all sinks connected to this source.\n\n"
          ":returns: list of sinks.")
      .def_static("enumerateSources", &VideoSource::EnumerateSources, release_gil(),
          "Enumerate all existing sources.\n\n"
          ":returns: list of sources.");
      //.def("__repr__", [](VideoSource &__inst){
      //  std::stringstream id;
      //  id << (void const *)&__inst;
      //  return std::string("<VideoSource name=") + __inst.GetName() + " kind=" + std::to_string(__inst.GetKind()) + " at" + id.str() + ">";
      //});
    
    py::enum_<VideoSource::Kind>(videosource, "Kind")
      .value("kUnknown", VideoSource::Kind::kUnknown)
      .value("kUsb", VideoSource::Kind::kUsb)
      .value("kHttp", VideoSource::Kind::kHttp)
      .value("kCv", VideoSource::Kind::kCv);
    
    py::enum_<VideoSource::ConnectionStrategy>(videosource, "ConnectionStrategy")
      .value("kAutoManage", VideoSource::kConnectionAutoManage)
      .value("kKeepOpen", VideoSource::kConnectionKeepOpen)
      .value("kForceClose", VideoSource::kConnectionForceClose);
    
    py::class_<VideoCamera, VideoSource> videocamera(m, "VideoCamera");
    videocamera.doc() = "A source that represents a video camera.";
    videocamera
      .def("setBrightness", &VideoCamera::SetBrightness, release_gil(),
           py::arg("brightness"),
           "Set the brightness, as a percentage (0-100).")
      .def("getBrightness", &VideoCamera::GetBrightness, release_gil(),
           "Get the brightness, as a percentage (0-100).")
      .def("setWhiteBalanceAuto", &VideoCamera::SetWhiteBalanceAuto, release_gil(),
           "Set the white balance to auto.")
      .def("setWhiteBalanceHoldCurrent", &VideoCamera::SetWhiteBalanceHoldCurrent, release_gil(),
           "Set the white balance to hold current.")
      .def("setWhiteBalanceManual", &VideoCamera::SetWhiteBalanceManual, release_gil(),
           py::arg("value"),
           "Set the white balance to manual, with specified color temperature.")
      .def("setExposureAuto", &VideoCamera::SetExposureAuto, release_gil(),
           "Set the exposure to auto aperature.")
      .def("setExposureHoldCurrent", &VideoCamera::SetExposureHoldCurrent, release_gil(),
           "Set the exposure to hold current.")
      .def("setExposureManual", &VideoCamera::SetExposureManual, release_gil(),
           py::arg("value"),
           "Set the exposure to manual, as a percentage (0-100).");
    
    py::enum_<VideoCamera::WhiteBalance>(videocamera, "WhiteBalance")
      .value("kFixedIndoor", VideoCamera::WhiteBalance::kFixedIndoor)
      .value("kFixedOutdoor1", VideoCamera::WhiteBalance::kFixedOutdoor1)
      .value("kFixedOutdoor2", VideoCamera::WhiteBalance::kFixedOutdoor2)
      .value("kFixedFluorescent1", VideoCamera::WhiteBalance::kFixedFluorescent1)
      .value("kFixedFlourescent2", VideoCamera::WhiteBalance::kFixedFlourescent2);
    
    py::class_<UsbCamera, VideoCamera> usbcamera(m, "UsbCamera");
    usbcamera.doc() = "A source that represents a USB camera.";
    usbcamera
      .def(py::init<const wpi::Twine&, int>(),
          py::arg("name"), py::arg("dev"),
          "Create a source for a USB camera based on device number.\n\n"
          ":param name: Source name (arbitrary unique identifier)\n"
          ":param dev: Device number (e.g. 0 for ``/dev/video0``)")
      .def(py::init<const wpi::Twine&, const wpi::Twine&>(),
          py::arg("name"), py::arg("path"),
          "Create a source for a USB camera based on device path.\n\n"
          ":param name: Source name (arbitrary unique identifier)\n"
          ":param path: Path to device (e.g. ``/dev/video0`` on Linux)")
      .def_static("enumerateUsbCameras", &UsbCamera::EnumerateUsbCameras, release_gil(),
          "Enumerate USB cameras on the local system.\n\n"
          ":returns: list of USB camera information (one for each camera)")
      .def("setPath", &UsbCamera::SetPath, release_gil(), py::arg("path"),
          "Change the path to the device.")
      .def("getPath", &UsbCamera::GetPath, "Get the path to the device.")
      .def("getInfo", &UsbCamera::GetInfo, release_gil(),
          "Get the full camera information for the device.")
      .def("setConnectVerbose", &UsbCamera::SetConnectVerbose, py::arg("level"),
           "Set how verbose the camera connection messages are.\n\n"
           ":param level: 0=don't display Connecting message, 1=do display message");

    py::class_<HttpCamera, VideoCamera> httpcamera(m, "HttpCamera");
    httpcamera.doc() = "A source that represents a MJPEG-over-HTTP (IP) camera.";
    
    // this has to come before the constructor definition
    py::enum_<HttpCamera::HttpCameraKind>(httpcamera, "HttpCameraKind")
      .value("kUnknown", HttpCamera::HttpCameraKind::kUnknown)
      .value("kMJPGStreamer", HttpCamera::HttpCameraKind::kMJPGStreamer)
      .value("kCSCore", HttpCamera::HttpCameraKind::kCSCore)
      .value("kAxis", HttpCamera::HttpCameraKind::kAxis);
    
    httpcamera
      //.def(py::init<wpi::StringRef,wpi::StringRef,HttpCamera::HttpCameraKind>())
      //.def(py::init<wpi::StringRef,const char *,cs::HttpCamera::HttpCameraKind>())
      .def(py::init<const wpi::Twine&, const wpi::Twine&, cs::HttpCamera::HttpCameraKind>(),
           py::arg("name"), py::arg("url"), py::arg("kind") = HttpCamera::HttpCameraKind::kUnknown,
          "Create a source for a MJPEG-over-HTTP (IP) camera.\n\n"
          ":param name: Source name (arbitrary unique identifier)\n"
          ":param url: Camera URL (e.g. \"http://10.x.y.11/video/stream.mjpg\")\n"
          ":param kind: Camera kind (e.g. kAxis)")
      .def(py::init<const wpi::Twine&, wpi::ArrayRef<std::string>, HttpCamera::HttpCameraKind>(),
           py::arg("name"), py::arg("urls"), py::arg("kind") = HttpCamera::HttpCameraKind::kUnknown,
          "Create a source for a MJPEG-over-HTTP (IP) camera.\n\n"
          ":param name: Source name (arbitrary unique identifier)\n"
          ":param urls: Array of Camera URLs\n"
          ":param kind: Camera kind (e.g. kAxis)")
      //.def(py::init<wpi::StringRef,std::initializer_list<T>,cs::HttpCamera::HttpCameraKind>())
      .def("getHttpCameraKind", &HttpCamera::GetHttpCameraKind, release_gil(),
          "Get the kind of HTTP camera. "
          "Autodetection can result in returning a different value than the camera was created with.")
      .def("setUrls", (void (HttpCamera::*)(wpi::ArrayRef<std::string>))&HttpCamera::SetUrls, release_gil(),
           py::arg("urls"),
           "Change the URLs used to connect to the camera.")
      //.def("SetUrls", (void (HttpCamera::*)(std::initializer_list<T>))&HttpCamera::SetUrls)
      .def("getUrls", &HttpCamera::GetUrls, release_gil(),
           "Get the URLs used to connect to the camera.");
    
    py::class_<AxisCamera, HttpCamera> axiscamera(m, "AxisCamera");
    axiscamera.doc() = "A source that represents an Axis IP camera.";
    axiscamera
      .def(py::init<const wpi::Twine&, const wpi::Twine&>(),
          py::arg("name"), py::arg("host"),
          "Create a source for a MJPEG-over-HTTP (IP) camera.\n\n"
          ":param name: Source name (arbitrary unique identifier)\n"
          ":param host: Camera host IP or DNS name (e.g. \"10.x.x.11\")\n"
          ":param kind: Camera kind (e.g. kAxis)")
      //.def(py::init<wpi::StringRef,const char *>(),
      //.def(py::init<wpi::StringRef,std::string>(),
      .def(py::init<const wpi::Twine&, wpi::ArrayRef<std::string>>(),
          py::arg("name"), py::arg("hosts"),
          "Create a source for a MJPEG-over-HTTP (IP) camera.\n\n"
          ":param name: Source name (arbitrary unique identifier)\n"
          ":param hosts: Array of Camera host IPs/DNS names\n"
          ":param kind: Camera kind (e.g. kAxis)");
      //.def(py::init<wpi::StringRef,std::initializer_list<T>>());
    
    py::class_<ImageSource, VideoSource> imagesource(m, "ImageSource");
    imagesource.doc() = "A base class for single image providing sources.";
    imagesource
      .def("notifyError", &ImageSource::NotifyError, release_gil(),
          py::arg("msg"),
          "Signal sinks that an error has occurred.  This should be called instead "
          "of :meth:`notifyFrame` when an error occurs.")
      .def("setConnected", &ImageSource::SetConnected, release_gil(),
          py::arg("connected"),
          "Set source connection status.  Defaults to true.\n\n"
          ":param connected: True for connected, false for disconnected")
      .def("setDescription", &ImageSource::SetDescription, release_gil(),
          py::arg("description"),
          "Set source description.\n\n"
          ":param description: Description")
      .def("createProperty", &ImageSource::CreateProperty, release_gil(),
          py::arg("name"), py::arg("kind"), py::arg("minimum"), py::arg("maximum"), py::arg("step"), py::arg("defaultValue"), py::arg("value"),
          "Create a property.\n\n"
          ":param name: Property name\n"
          ":param kind: Property kind\n"
          ":param minimum: Minimum value\n"
          ":param maximum: Maximum value\n"
          ":param step: Step value\n"
          ":param defaultValue: Default value\n"
          ":param value: Current value\n\n"
          ":returns: Property\n")
      .def("createIntegerProperty", &ImageSource::CreateIntegerProperty, release_gil(),
          py::arg("name"), py::arg("minimum"), py::arg("maximum"), py::arg("step"), py::arg("defaultValue"), py::arg("value"),
          "Create a property.\n\n"
          ":param name: Property name\n"
          ":param minimum: Minimum value\n"
          ":param maximum: Maximum value\n"
          ":param step: Step value\n"
          ":param defaultValue: Default value\n"
          ":param value: Current value\n\n"
          ":returns: Property\n")
      .def("createBooleanProperty", &ImageSource::CreateBooleanProperty, release_gil(),
          py::arg("name"), py::arg("defaultValue"), py::arg("value"),
          "Create a property.\n\n"
          ":param name: Property name\n"
          ":param defaultValue: Default value\n"
          ":param value: Current value\n\n"
          ":returns: Property\n")
      .def("createStringProperty", &ImageSource::CreateStringProperty, release_gil(),
          py::arg("name"), py::arg("value"),
          "Create a property.\n\n"
          ":param name: Property name\n"
          ":param value: Current value\n\n"
          ":returns: Property\n")
      .def("setEnumPropertyChoices", (void (ImageSource::*)(const VideoProperty &property, wpi::ArrayRef<std::string> choices))&ImageSource::SetEnumPropertyChoices, release_gil(),
          py::arg("property"), py::arg("choices"),
          "Configure enum property choices.\n\n"
          ":param property: Property\n"
          ":param choices: Choices");
      /*.def("SetEnumPropertyChoices", [](ImageSource &__inst, std::initializer_list<T> choices) {
        cs::VideoProperty property;
        auto __ret = __inst.SetEnumPropertyChoices(property, choices);
        return std::make_tuple(__ret, property);
    });*/

    py::class_<VideoSink> videosink(m, "VideoSink");
    videosink.doc() = "A sink for video that accepts a sequence of frames.";
    videosink
      .def(py::init<cs::VideoSink>(), py::arg("sink"))
      .def("getHandle", &VideoSink::GetHandle)
      .def(py::self == py::self)
      .def(py::self != py::self)
      .def("getKind", &VideoSink::GetKind, release_gil(),
          "Get the kind of the sink.")
      .def("getName", &VideoSink::GetName, release_gil(),
          "Get the name of the sink.  The name is an arbitrary identifier "
          "provided when the sink is created, and should be unique.")
      .def("getDescription", &VideoSink::GetDescription, release_gil(),
          "Get the sink description.  This is sink-kind specific.")
      .def("getProperty", &VideoSink::GetProperty, py::arg("name"), release_gil(),
          "Get a property.\n\n"
          ":param name: Property name\n"
          ":returns: Property contents (VideoSource.Kind.kNone if no property with the given name exists)")
      .def("enumerateProperties", &VideoSink::EnumerateProperties, release_gil(),
          "Enumerate all properties of this sink")
      .def("setConfigJson", [](VideoSink &__inst, wpi::StringRef config) {
        py::gil_scoped_release __release;
        return __inst.SetConfigJson(config);
      }, py::arg("config"),
        "Set properties from a JSON configuration string.\n\n"
        "The format of the JSON input is::\n\n"
        "    {\n"
        "      \"properties\": [\n"
        "        {\n"
        "          \"name\": \"property name\",\n"
        "          \"value\": \"property value\"\n"
        "         }\n"
        "      ]\n"
        "    }\n\n"
        ":param config: configuration\n"
        ":returns: True if set successfully")
      .def("getConfigJson", &VideoSink::GetConfigJson, release_gil(),
          "Get a JSON configuration string.\n\n"
          ":returns: JSON configuration string\n")
      .def("setSource", &VideoSink::SetSource, release_gil(),
          py::arg("source"),
          "Configure which source should provide frames to this sink.  Each sink "
          "can accept frames from only a single source, but a single source can "
          "provide frames to multiple clients.\n\n"
          ":param source: Source")
      .def("getSource", &VideoSink::GetSource, release_gil(),
          "Get the connected source.\n\n"
          ":returns: Connected source (empty if none connected).")
      .def("getSourceProperty", &VideoSink::GetSourceProperty, release_gil(),
          py::arg("name"),
          "Get a property of the associated source.\n\n"
          ":param name: Property name\n"
          ":returns: Property (VideoSink.Kind.kNone if no property with the given name exists or no source connected)")
      .def("getLastStatus", &VideoSink::GetLastStatus)
      .def_static("enumerateSinks", &VideoSink::EnumerateSinks, release_gil(),
          "Enumerate all existing sinks.\n\n"
          ":returns: list of sinks.");
    
    py::enum_<VideoSink::Kind>(videosink, "Kind")
      .value("kUnknown", VideoSink::Kind::kUnknown)
      .value("kMjpeg", VideoSink::Kind::kMjpeg)
      .value("kCv", VideoSink::Kind::kCv);
    
    py::class_<MjpegServer, VideoSink> mjpegserver(m, "MjpegServer");
    mjpegserver.doc() = "A sink that acts as a MJPEG-over-HTTP network server.";
    mjpegserver
      .def(py::init<const wpi::Twine&, const wpi::Twine&, int>(),
          py::arg("name"), py::arg("listenAddress"), py::arg("port"),
          "Create a MJPEG-over-HTTP server sink.\n\n"
          ":param name: Sink name (arbitrary unique identifier)\n"
          ":param listenAddress: TCP listen address (empty string for all addresses)\n"
          ":param port: TCP port number")
      .def(py::init<const wpi::Twine&, int>(),
          py::arg("name"), py::arg("port"),
          "Create a MJPEG-over-HTTP server sink.\n\n"
          ":param name: Sink name (arbitrary unique identifier)\n"
          ":param port: TCP port number")
      .def("getListenAddress", &MjpegServer::GetListenAddress, "Get the listen address of the server.")
      .def("getPort", &MjpegServer::GetPort, "Get the port number of the server.")
      .def("setResolution", &MjpegServer::SetResolution, py::arg("width"), py::arg("height"), release_gil(),
          "Set the stream resolution for clients that don't specify it.\n\n"
          "It is not necessary to set this if it is the same as the source "
          "resolution.\n\n"
          "Setting this different than the source resolution will result in "
          "increased CPU usage, particularly for MJPEG source cameras, as it will "
          "decompress, resize, and recompress the image, instead of using the "
          "camera's MJPEG image directly.\n\n"
          ":param width:  width, 0 for unspecified\n"
          ":param height: height, 0 for unspecified")
      .def("setFPS", &MjpegServer::SetFPS, py::arg("fps"), release_gil(),
          "Set the stream frames per second (FPS) for clients that don't specify it.\n\n"
          "It is not necessary to set this if it is the same as the source FPS.\n\n"
          ":param fps: FPS, 0 for unspecified")
      .def("setCompression", &MjpegServer::SetCompression, py::arg("quality"), release_gil(),
          "Set the compression for clients that don't specify it.\n\n"
          "Setting this will result in increased CPU usage for MJPEG source cameras "
          "as it will decompress and recompress the image instead of using the "
          "camera's MJPEG image directly.\n\n"
          ":param quality: JPEG compression quality (0-100), -1 for unspecified")
      .def("setDefaultCompression", &MjpegServer::SetDefaultCompression, py::arg("quality"), release_gil(),
           "Set the default compression used for non-MJPEG sources.  If not set, "
           "80 is used.  This function has no effect on MJPEG source cameras; use "
           "setCompression() instead to force recompression of MJPEG source images.\n\n"
           ":param quality: JPEG compression quality (0-100)");
    
    py::class_<ImageSink, VideoSink> imagesink(m, "ImageSink");
    imagesink.doc() = "A base class for single image reading sinks.";
    imagesink
      .def("setDescription", &ImageSink::SetDescription,
          py::arg("description"),
          "Set sink description.\n\n"
          ":param description: Description")
      .def("getError", &ImageSink::GetError,
           "Get error string.  Call this if :meth:`waitForFrame` returns 0 to determine what the error is.")
      .def("setEnabled", &ImageSink::SetEnabled,
          py::arg("enabled"),
          "Enable or disable getting new frames.\n"
          "Disabling will cause processFrame (for callback-based ImageSinks) to not"
          " be called and :meth:`waitForFrame` to not return.  This can be used to save"
          " processor resources when frames are not needed.");
    
    py::class_<RawEvent> rawevent(m, "RawEvent");
    rawevent.doc() = "Listener event";
    rawevent
      .def_readonly("kind", &RawEvent::kind)
      .def_readonly("mode", &RawEvent::mode)
      .def_readonly("name", &RawEvent::name)
      .def_readonly("value", &RawEvent::value)
      .def_readonly("valueStr", &RawEvent::valueStr)
      .def_readonly("sourceHandle", &RawEvent::sourceHandle)
      .def_readonly("sinkHandle", &RawEvent::sinkHandle);
    
    py::enum_<RawEvent::Kind>(rawevent, "Kind")
      .value("kSourceCreated", RawEvent::Kind::kSourceCreated)
      .value("kSourceDestroyed", RawEvent::Kind::kSourceDestroyed)
      .value("kSourceConnected", RawEvent::Kind::kSourceConnected)
      .value("kSourceDisconnected", RawEvent::Kind::kSourceDisconnected)
      .value("kSourceVideoModesUpdated", RawEvent::Kind::kSourceVideoModesUpdated)
      .value("kSourceVideoModeChanged", RawEvent::Kind::kSourceVideoModeChanged)
      .value("kSourcePropertyCreated", RawEvent::Kind::kSourcePropertyCreated)
      .value("kSourcePropertyValueUpdated", RawEvent::Kind::kSourcePropertyValueUpdated)
      .value("kSourcePropertyChoicesUpdated", RawEvent::Kind::kSourcePropertyChoicesUpdated)
      .value("kSinkSourceChanged", RawEvent::Kind::kSinkSourceChanged)
      .value("kSinkCreated", RawEvent::Kind::kSinkCreated)
      .value("kSinkDestroyed", RawEvent::Kind::kSinkDestroyed)
      .value("kSinkEnabled", RawEvent::Kind::kSinkEnabled)
      .value("kSinkDisabled", RawEvent::Kind::kSinkDisabled)
      .value("kNetworkInterfacesChanged", RawEvent::Kind::kNetworkInterfacesChanged)
      .value("kTelemetryUpdated", RawEvent::Kind::kTelemetryUpdated)
      .value("kSinkPropertyCreated", RawEvent::Kind::kSinkPropertyCreated)
      .value("kSinkPropertyValueUpdated", RawEvent::Kind::kSinkPropertyValueUpdated)
      .value("kSinkPropertyChoicesUpdated", RawEvent::Kind::kSinkPropertyChoicesUpdated);
    
    py::class_<VideoEvent, RawEvent> videoevent(m, "VideoEvent");
    videoevent.doc() = "An event generated by the library and provided to event listeners.";
    videoevent
      .def("getSource", &VideoEvent::GetSource)
      .def("getSink", &VideoEvent::GetSink)
      .def("getProperty", &VideoEvent::GetProperty);
      
    
    py::class_<VideoListenerWrapper> videolistener(m, "VideoListener");
    videolistener.doc() = 
        "An event listener.  This calls back to a desigated callback function when\n"
        "an event matching the specified mask is generated by the library.";
    videolistener
      .def(py::init<std::function<void(const VideoEvent&)>,int,bool>(),
          py::arg("callback"), py::arg("eventMask"), py::arg("immediateNotify"),
          "Create an event listener.\n\n"
          ":param callback: Callback function\n"
          ":param eventMask: Bitmask of VideoEvent.Kind values\n"
          ":param immediateNotify: Whether callback should be immediately called with"
          " a representative set of events for the current library state.");

    // now in cscore_cv.h

    py::class_<CvSource, ImageSource> cvsource(m, "CvSource");
    cvsource.doc() = "A source for user code to provide OpenCV images as video frames.";
    cvsource
      .def(py::init<const wpi::Twine&, VideoMode>(),
          py::arg("name"), py::arg("mode"),
          "Create an OpenCV source.\n\n"
          ":param name: Source name (arbitrary unique identifier)\n"
          ":param mode: Video mode being generated")
      .def(py::init<const wpi::Twine&, VideoMode::PixelFormat, int, int, int>(),
          py::arg("name"), py::arg("pixelFormat"), py::arg("width"), py::arg("height"), py::arg("fps"),
          "Create an OpenCV source.\n\n"
          ":param name: Source name (arbitrary unique identifier)\n"
          ":param pixelFormat: Pixel format\n"
          ":param width: width\n"
          ":param height: height\n"
          ":param fps: fps")
      .def("putFrame", &CvSource::PutFrame, release_gil(),
          py::arg("image"),
          "Put an OpenCV image and notify sinks.\n\n"
          "Only 8-bit single-channel or 3-channel (with BGR channel order) images "
          "are supported. If the format, depth or channel order is different, use "
          "``cv2.convertTo()`` and/or ``cv2.cvtColor()`` to convert it first.\n\n"
          ":param image: OpenCV image");

    py::class_<CvSink, ImageSink> cvsink(m, "CvSink");
    cvsink.doc() = "A sink for user code to accept video frames as OpenCV images.";
    cvsink
      .def(py::init<const wpi::Twine&>(),
          py::arg("name"),
          "Create a sink for accepting OpenCV images. "
          ":meth:`grabFrame` must be called on the created sink to get each new image\n\n"
          ":param name: Source name (arbitrary unique identifier)")
      /*.def(py::init<wpi::StringRef,std::function<void(uint64_t)>>(),
          py::arg("name"), py::arg("processFrame"),
          "Create a sink for accepting OpenCV images in a separate thread. "
          "A thread will be created that calls the "
          "``processFrame`` callback each time a new frame arrives.\n\n"
          ":param name: Source name (arbitrary unique identifier)\n"
          ":param processFrame: Frame processing function; will be called with a "
          "time=0 if an error occurred.  processFrame should call :meth:`grabFrame`"
          "or :meth:`getError` as needed.")*/
      .def("setDescription", &CvSink::SetDescription,
          py::arg("description"),
          "Set sink description.\n\n"
          ":param description: Description")
      .def("grabFrame", [](CvSink &__inst, cv::Mat &image, double timeout) {
        py::gil_scoped_release release;
        auto __ret = __inst.GrabFrame(image, timeout);
        return std::make_tuple(__ret, image);
      }, py::arg("image"), py::arg("timeout") = 0.225,
          "Wait for the next frame and get the image. Times out (returning 0) after timeout seconds.\n"
          "The provided image will have three 8-bit channels stored in BGR order.\n\n"
          ":returns: Frame time, or 0 on error (call :meth:`getError` to obtain the error message), returned image\n"
          "          The frame time is in 1us increments"
      )
      .def("grabFrameNoTimeout", [](CvSink &__inst, cv::Mat &image) {
          py::gil_scoped_release release;
          auto __ret = __inst.GrabFrameNoTimeout(image);
          return std::make_tuple(__ret, image);
        }, py::arg("image"),
          "Wait for the next frame and get the image. May block forever.\n"
          "The provided image will have three 8-bit channels stored in BGR order.\n\n"
          ":returns: Frame time, or 0 on error (call :meth:`getError` to obtain the error message), returned image\n"
          "          The frame time is in 1us increments"
        );
}
