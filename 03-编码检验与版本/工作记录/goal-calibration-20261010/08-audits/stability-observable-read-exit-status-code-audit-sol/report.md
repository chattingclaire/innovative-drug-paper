稳定性接收代码也存在同类整command退出码假阴性入口，但本任务未审读任何实际稳定性事件，不能报告它已发生。

external-capture-v2的receiver.py:105只有item.completed + command_execution + exit_code==0 + 完整payload匹配才记录读取；103–108行令exit1中的完整块同样不计。transport_common.py:220–227绑定path/SHA/start/end/token，payload包含完整BEGIN、正文、END；read_allowed.py:14–16在单块打印前校验范围。若同一外层command先打印完整合法块、以后另一块失败，整item exit1会令之前的完整块被拒。

capacity13没有独立修正：controller.py:8–12调用bootstrap.runtime；bootstrap.py:13–26直接加载封存receiver，17–21只改controller并发字符串。实际profile的receiver绑定SHA为534be942f5a7944c9e05918134dd538ae13b0827e6f3feaebec26208c335face。其后外部controller→receiver.receive_locked:239→verify_capture:72–73→capture-validator.verify；外层完整块匹配仍在105行。

共用native strict_reception_guard.py:58–65派发base-validator，100–109核实际CLI整体终止/returncode0/未超时及fresh thread/turn；不按工具command退出码丢块。native0216的独立observable_reads层strict-readback-receiver.py:42才有整item skip（当前绑定文件精确行号），与稳定性105行同类。稳定性用capture-validator而非该actor-file guard；其CLI整体完成检查在receiver.py:19–26及48–57，声明的完整范围覆盖在capture-validator.py:130–137。必须区分CLI整体返回码、provider turn完成、单个command返回码、某读块完整四件事。

至多建议另封外层兼容：对唯一first之前的真实completed command，逐块核完整且精确绑定的payload，允许后续失败导致的非零command状态，原exit_code保留于证据；不要把事件改成exit0。整体CLI/turn、独占首答、绑定/全文覆盖、缺END或错正文等原guard不放宽。这里只报告建议，未建补丁、未改冻结文件、未运行任何receiver/分类器/模型，未读800或200正文答案。
