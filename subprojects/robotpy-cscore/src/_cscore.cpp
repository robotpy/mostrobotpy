
#include <pybind11/pybind11.h>
#include <pybind11/functional.h>
#include <pybind11/operators.h>
#include <pybind11/stl.h>
#include "release_gil.hpp"
namespace py = pybind11;

#include "cscore_oo.h"
using namespace cs;

#include <opencv2/opencv.hpp>

#include "ndarray_converter.h"
#include "wpiutil_converters.hpp"


PYBIND11_PLUGIN(_cscore) {

    NDArrayConverter::init_numpy();

    py::module m("_cscore");
    
    static int unused; // the capsule needs something to reference
    py::capsule cleanup(&unused, [](PyObject *) {
        // don't release gil until after calling this
        SetDefaultLogger(20 /* WPI_LOG_INFO */);
        
        // but this MUST release the gil, or deadlock may occur
        py::gil_scoped_release __release;
        CS_Destroy();
    });
    m.add_object("_cleanup", cleanup);
    
    // cscore_cpp.h
    
    py::class_<UsbCameraInfo> usbcamerainfo(m, "UsbCameraInfo");
    usbcamerainfo
      .def_readwrite("dev", &UsbCameraInfo::dev)
      .def_readwrite("path", &UsbCameraInfo::path)
      .def_readwrite("name", &UsbCameraInfo::name)
      .def("__repr__", [](UsbCameraInfo &__inst){
         return std::string("<UsbCameraInfo dev=") + std::to_string(__inst.dev) + " path=" + __inst.path + " name=" + __inst.name + ">";
       });
    
    py::class_<CS_VideoMode> cs_videomode(m, "_CS_VideoMode");
    
    py::class_<VideoMode, CS_VideoMode> videomode(m, "VideoMode");
    videomode
      .def(py::init<>())
      .def(py::init<cs::VideoMode::PixelFormat,int,int,int>())
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
    
    #define def_status_fn(n, N, T) def(n, [](T t) { py::gil_scoped_release __r; CS_Status s = 0; return N(t, &s); })
    
    m.def("getNetworkInterfaces", &GetNetworkInterfaces)
     .def_status_fn("getHttpCameraUrls", GetHttpCameraUrls, CS_Source)
     .def_status_fn("getMjpegServerPort", GetHttpCameraUrls, CS_Sink)
     .def("getMjpegServerListenAddress", &GetMjpegServerListenAddress)
     .def_status_fn("getUsbCameraPath", GetUsbCameraPath, CS_Source)
     .def("setLogger", &SetLogger);
     
    // cscore_oo.h

    py::class_<VideoProperty> videoproperty(m, "VideoProperty");
    videoproperty
      .def(py::init<>())
      .def("getName", py::release_gil(&VideoProperty::GetName))
      .def("getKind", py::release_gil(&VideoProperty::GetKind))
      .def("isBoolean", py::release_gil(&VideoProperty::IsBoolean))
      .def("isInteger", py::release_gil(&VideoProperty::IsInteger))
      .def("isString", py::release_gil(&VideoProperty::IsString))
      .def("isEnum", py::release_gil(&VideoProperty::IsEnum))
      .def("get", py::release_gil(&VideoProperty::Get))
      .def("set", py::release_gil(&VideoProperty::Set))
      .def("getMin", py::release_gil(&VideoProperty::GetMin))
      .def("getMax", py::release_gil(&VideoProperty::GetMax))
      .def("getStep", py::release_gil(&VideoProperty::GetStep))
      .def("getDefault", py::release_gil(&VideoProperty::GetDefault))
      .def("getString", py::release_gil((std::string (VideoProperty::*)() const)&VideoProperty::GetString))
      /*.def("GetString", [](VideoProperty &__inst) {
        llvm::SmallVectorImpl<char> buf;
        auto __ret = __inst.GetString(buf);
        return std::make_tuple(__ret, buf);
      })*/
      .def("setString", py::release_gil(&VideoProperty::SetString))
      .def("getChoices", py::release_gil(&VideoProperty::GetChoices))
      .def("getLastStatus", py::release_gil(&VideoProperty::GetLastStatus));
    
    py::enum_<VideoProperty::Kind>(videoproperty, "Kind")
      .value("kNone", VideoProperty::Kind::kNone)
      .value("kBoolean", VideoProperty::Kind::kBoolean)
      .value("kInteger", VideoProperty::Kind::kInteger)
      .value("kString", VideoProperty::Kind::kString)
      .value("kEnum", VideoProperty::Kind::kEnum);
    
    py::class_<VideoSource> videosource(m, "VideoSource");
    videosource
      .def(py::init<>())
      .def(py::init<cs::VideoSource>())
      .def(py::init<cs::VideoSource>())
      .def("getHandle", &VideoSource::GetHandle)
      .def(py::self == py::self)
      .def(py::self != py::self)
      .def("getKind", &VideoSource::GetKind)
      .def("getName", &VideoSource::GetName)
      .def("getDescription", &VideoSource::GetDescription)
      .def("getLastFrameTime", &VideoSource::GetLastFrameTime)
      .def("isConnected", &VideoSource::IsConnected)
      .def("getProperty", py::release_gil(&VideoSource::GetProperty))
      .def("enumerateProperties", py::release_gil(&VideoSource::EnumerateProperties))
      .def("getVideoMode", py::release_gil(&VideoSource::GetVideoMode))
      .def("setVideoMode", [](VideoSource &__inst, VideoMode mode) {
        py::gil_scoped_release __release;
        return __inst.SetVideoMode(mode);
      })
      .def("setVideoMode", [](VideoSource &__inst, VideoMode::PixelFormat pixelFormat, int width, int height, int fps) {
        py::gil_scoped_release __release;
        return __inst.SetVideoMode(pixelFormat, width, height, fps);
      })
      .def("setPixelFormat", py::release_gil(&VideoSource::SetPixelFormat))
      .def("setResolution", py::release_gil(&VideoSource::SetResolution))
      .def("setFPS", py::release_gil(&VideoSource::SetFPS))
      .def("enumerateVideoModes", py::release_gil(&VideoSource::EnumerateVideoModes))
      .def("getLastStatus", py::release_gil(&VideoSource::GetLastStatus))
      .def("enumerateSinks", py::release_gil(&VideoSource::EnumerateSinks))
      .def_static("enumerateSources", py::release_gil(&VideoSource::EnumerateSources));
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
    
    py::class_<VideoCamera, VideoSource> videocamera(m, "VideoCamera");
    videocamera
      .def(py::init<>())
      .def("setBrightness", py::release_gil(&VideoCamera::SetBrightness))
      .def("getBrightness", py::release_gil(&VideoCamera::GetBrightness))
      .def("setWhiteBalanceAuto", py::release_gil(&VideoCamera::SetWhiteBalanceAuto))
      .def("setWhiteBalanceHoldCurrent", py::release_gil(&VideoCamera::SetWhiteBalanceHoldCurrent))
      .def("setWhiteBalanceManual", py::release_gil(&VideoCamera::SetWhiteBalanceManual))
      .def("setExposureAuto", py::release_gil(&VideoCamera::SetExposureAuto))
      .def("setExposureHoldCurrent", py::release_gil(&VideoCamera::SetExposureHoldCurrent))
      .def("setExposureManual", py::release_gil(&VideoCamera::SetExposureManual));
    
    py::enum_<VideoCamera::WhiteBalance>(videocamera, "WhiteBalance")
      .value("kFixedIndoor", VideoCamera::WhiteBalance::kFixedIndoor)
      .value("kFixedOutdoor1", VideoCamera::WhiteBalance::kFixedOutdoor1)
      .value("kFixedOutdoor2", VideoCamera::WhiteBalance::kFixedOutdoor2)
      .value("kFixedFluorescent1", VideoCamera::WhiteBalance::kFixedFluorescent1)
      .value("kFixedFlourescent2", VideoCamera::WhiteBalance::kFixedFlourescent2);
    
#ifdef __linux__
    py::class_<UsbCamera, VideoCamera> usbcamera(m, "UsbCamera");
    usbcamera
      .def(py::init<>())
      .def(py::init<llvm::StringRef,int>())
      .def(py::init<llvm::StringRef,llvm::StringRef>())
      .def_static("enumerateUsbCameras", py::release_gil(&UsbCamera::EnumerateUsbCameras))
      .def("getPath", &UsbCamera::GetPath);
#endif

    py::class_<HttpCamera, VideoCamera> httpcamera(m, "HttpCamera");
    
    // this has to come before the constructor definition
    py::enum_<HttpCamera::HttpCameraKind>(httpcamera, "HttpCameraKind")
      .value("kUnknown", HttpCamera::HttpCameraKind::kUnknown)
      .value("kMJPGStreamer", HttpCamera::HttpCameraKind::kMJPGStreamer)
      .value("kCSCore", HttpCamera::HttpCameraKind::kCSCore)
      .value("kAxis", HttpCamera::HttpCameraKind::kAxis);
    
    httpcamera
      //.def(py::init<llvm::StringRef,llvm::StringRef,HttpCamera::HttpCameraKind>())
      //.def(py::init<llvm::StringRef,const char *,cs::HttpCamera::HttpCameraKind>())
      .def(py::init<llvm::StringRef,std::string,cs::HttpCamera::HttpCameraKind>(),
           py::arg("name"), py::arg("url"), py::arg("kind") = HttpCamera::HttpCameraKind::kUnknown)
      .def(py::init<llvm::StringRef,llvm::ArrayRef<std::string>,HttpCamera::HttpCameraKind>(),
           py::arg("name"), py::arg("urls"), py::arg("kind") = HttpCamera::HttpCameraKind::kUnknown)
      //.def(py::init<llvm::StringRef,std::initializer_list<T>,cs::HttpCamera::HttpCameraKind>())
      .def("getHttpCameraKind", py::release_gil(&HttpCamera::GetHttpCameraKind))
      .def("setUrls", py::release_gil((void (HttpCamera::*)(llvm::ArrayRef<std::string>))&HttpCamera::SetUrls))
      //.def("SetUrls", (void (HttpCamera::*)(std::initializer_list<T>))&HttpCamera::SetUrls)
      .def("getUrls", py::release_gil(&HttpCamera::GetUrls));
    
    py::class_<AxisCamera, HttpCamera> axiscamera(m, "AxisCamera");
    axiscamera
      .def(py::init<llvm::StringRef,llvm::StringRef>())
      .def(py::init<llvm::StringRef,const char *>())
      .def(py::init<llvm::StringRef,std::string>())
      .def(py::init<llvm::StringRef,llvm::ArrayRef<std::string>>());
      //.def(py::init<llvm::StringRef,std::initializer_list<T>>());
    
    py::class_<CvSource, VideoSource> cvsource(m, "CvSource");
    cvsource
      .def(py::init<>())
      .def(py::init<llvm::StringRef,VideoMode>())
      .def(py::init<llvm::StringRef,VideoMode::PixelFormat,int,int,int>())
      .def("putFrame", [](CvSource &__inst, cv::Mat &image) {
        py::gil_scoped_release release;
        __inst.PutFrame(image);
      })
      .def("notifyError", &CvSource::NotifyError)
      .def("setConnected", &CvSource::SetConnected)
      .def("setDescription", &CvSource::SetDescription)
      .def("createProperty", py::release_gil(&CvSource::CreateProperty))
      .def("setEnumPropertyChoices", py::release_gil((void (CvSource::*)(const VideoProperty &property, llvm::ArrayRef<std::string> choices))&CvSource::SetEnumPropertyChoices));
      /*.def("SetEnumPropertyChoices", [](CvSource &__inst, std::initializer_list<T> choices) {
        cs::VideoProperty property;
        auto __ret = __inst.SetEnumPropertyChoices(property, choices);
        return std::make_tuple(__ret, property);
    });*/
    
    py::class_<VideoSink> videosink(m, "VideoSink");
    videosink
      .def(py::init<>())
      .def(py::init<cs::VideoSink>())
      .def(py::init<cs::VideoSink>())
      .def("getHandle", &VideoSink::GetHandle)
      .def(py::self == py::self)
      .def(py::self != py::self)
      .def("getKind", &VideoSink::GetKind)
      .def("getName", &VideoSink::GetName)
      .def("getDescription", &VideoSink::GetDescription)
      .def("setSource", py::release_gil(&VideoSink::SetSource))
      .def("getSource", py::release_gil(&VideoSink::GetSource))
      .def("getSourceProperty", py::release_gil(&VideoSink::GetSourceProperty))
      .def("getLastStatus", &VideoSink::GetLastStatus)
      .def_static("enumerateSinks", py::release_gil(&VideoSink::EnumerateSinks));
    
    py::enum_<VideoSink::Kind>(videosink, "Kind")
      .value("kUnknown", VideoSink::Kind::kUnknown)
      .value("kMjpeg", VideoSink::Kind::kMjpeg)
      .value("kCv", VideoSink::Kind::kCv);
    
    py::class_<MjpegServer, VideoSink> mjpegserver(m, "MjpegServer");
    mjpegserver
      .def(py::init<>())
      .def(py::init<llvm::StringRef,llvm::StringRef,int>())
      .def(py::init<llvm::StringRef,int>())
      .def("getListenAddress", &MjpegServer::GetListenAddress)
      .def("getPort", &MjpegServer::GetPort);
    
    py::class_<CvSink, VideoSink> cvsink(m, "CvSink");
    cvsink
      .def(py::init<>())
      .def(py::init<llvm::StringRef>())
      .def(py::init<llvm::StringRef,std::function<void(uint64_t)>>())
      .def("setDescription", &CvSink::SetDescription)
      .def("grabFrame", [](CvSink &__inst, cv::Mat &image) {
        py::gil_scoped_release release;
        auto __ret = __inst.GrabFrame(image);
        return std::make_tuple(__ret, image);
      })
      .def("getError", &CvSink::GetError)
      .def("setEnabled", &CvSink::SetEnabled);
    
    py::class_<RawEvent> rawevent(m, "RawEvent");
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
      .value("kNetworkInterfacesChanged", RawEvent::Kind::kNetworkInterfacesChanged);
    
    py::class_<VideoEvent, RawEvent> videoevent(m, "VideoEvent");
    videoevent
      .def("getSource", &VideoEvent::GetSource)
      .def("getSink", &VideoEvent::GetSink)
      .def("getProperty", &VideoEvent::GetProperty);
      
    
    py::class_<VideoListener> videolistener(m, "VideoListener");
    videolistener
      .def(py::init<std::function<void(const VideoEvent&)>,int,bool>());

    return m.ptr();
}
