# tools/dump-vbios

dump-vbios.ps1 — 通过 NvAPI_QueryInterface 调 NvAPI_GPU_GetVbiosImage 的尝试。

结果:该卡上返回 -9,此路不通;最终用 nvflashk --save。
留档价值:展示了 NvAPI 私有接口的调用姿势(0xFC13EE11 等接口 id),
在别的卡上可能直接可用。