import logging
import twain
import sys
from tkinter import *
from tkinter import messagebox
import traceback
import os
from datetime import datetime
from typing import List, Dict, Tuple, Literal, Optional
import time
from twain import exceptions
from twain.lowlevel import constants

log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)
# 生成日志文件名（使用当前时间戳）
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(log_directory, f"scan_log_{current_time}.log")

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=log_filename,
    filemode='w'
)

root = Tk()
output_directory = r"D:\code\DSPS\DSPS\20240711scan\pytwain-master\demo"
if not os.path.exists(output_directory):
    os.makedirs(output_directory)
    logging.info(f"创建输出目录: {output_directory}")
def scan():
    logging.info("开始扫描过程")
    try:
        outpath = output_directory
        logging.info(f"输出路径: {outpath}")
        result = acquire(
            outpath,
            dpi=300,
            frame=(0, 0, 8.17551, 11.45438),  # A4
            pixel_type="color",
        )
        logging.info(f"扫描结果: {result}")
    except Exception as e:
        logging.error(f"扫描过程中发生错误: {str(e)}")
        logging.error(traceback.format_exc())
        messagebox.showerror("Error", traceback.format_exc())
        sys.exit(1)
    else:
        if result:
            logging.info(f"扫描成功,图像保存在: {outpath}")
            messagebox.showinfo("Success", f"Image saved as: {outpath}")
            sys.exit(1)
        else:
            logging.error("扫描失败")
            messagebox.showerror("Error", "Scan failed.")
            sys.exit(1)
def acquire(
        path: str,
        ds_name: Optional[str] = None,
        dpi: Optional[float] = None,
        pixel_type: Optional[Literal["bw", "gray", "color"]] = "color",
        bpp: Optional[int] = None,
        frame: Optional[Tuple[float, float, float, float]] = None,
        parent_window=None,
        show_ui: bool = False,
        dsm_name: Optional[str] = None,
        modal: bool = False,
) -> Optional[List[Dict]]:
    logging.info(f"开始acquire函数,参数: path={path}, dpi={dpi}, pixel_type={pixel_type}, frame={frame}")
    if pixel_type:
        pixel_type_map = {
            "bw": constants.TWPT_BW,
            "gray": constants.TWPT_GRAY,
            "color": constants.TWPT_RGB,
        }
        twain_pixel_type = pixel_type_map[pixel_type]
        logging.info(f"设置像素类型: {twain_pixel_type}")
    else:
        twain_pixel_type = None
    dsm_name = "KODAK Scanner: i2000"
    logging.info(f"使用扫描仪: {dsm_name}")
    sm = twain.SourceManager(0, 0)
    logging.info("创建SourceManager对象")
    page_number = 0
    try:
        sd = sm.open_source(dsm_name)
        if not sd:
            logging.error("无法打开数据源")
            return None
        logging.info("成功打开数据源")
        try:
            if twain_pixel_type:
                sd.set_capability(constants.ICAP_PIXELTYPE, constants.TWTY_UINT16, twain_pixel_type)
            sd.set_capability(constants.ICAP_UNITS, constants.TWTY_UINT16, constants.TWUN_INCHES)
            #是否双面打印
            sd.set_capability(constants.CAP_DUPLEXENABLED, constants.TWTY_BOOL, True)
            if bpp:
                sd.set_capability(constants.ICAP_BITDEPTH, constants.TWTY_UINT16, bpp)
            if dpi:
                sd.set_capability(constants.ICAP_XRESOLUTION, constants.TWTY_FIX32, dpi)
                sd.set_capability(constants.ICAP_YRESOLUTION, constants.TWTY_FIX32, dpi)
            if frame:
                try:
                    sd.set_image_layout(frame)
                except exceptions.CheckStatus:
                    logging.warning("设置图像布局失败")
            logging.info("设置扫描参数完成")
            res: List[Dict] = []
            def before(img_info: Dict) -> str:
                nonlocal page_number
                page_number += 1
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"scan_{timestamp}_{page_number:03d}.png"
                full_path = os.path.join(path, file_name)
                res.append(img_info)
                logging.info(f"准备扫描第 {page_number} 页,文件路径: {full_path}")
                return full_path
            def after(more: int) -> None:
                if more==0:
                    logging.info("扫描完成,没有更多页面")
                    # raise exceptions.CancelAll
                else:
                    logging.info(f"还有 {more} 页需要扫描")
            try:
                sd.acquire_file(before=before, after=after, show_ui=show_ui, modal=modal)
                logging.info("扫描操作完成")
            except exceptions.DSTransferCancelled:
                logging.info("用户取消了扫描")
                return None
        finally:
            sd.close()
            logging.info("关闭数据源")
    finally:
        sm.close()
        logging.info("关闭SourceManager")
    logging.info(f"扫描结果: {res}")
    return res

logging.info("程序开始运行")
root.after(1, scan)
logging.info("设置1毫秒后开始扫描")
root.mainloop()
logging.info("程序结束")
