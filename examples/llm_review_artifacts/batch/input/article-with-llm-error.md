# LLM Partial Failure 示例

这篇短文用于展示 batch LLM partial failure。

Deterministic review 仍然可以完成，但 LLM sidecar 会把该文件记为 failed。

这样可以在不改变 deterministic quality gate 的前提下，单独检查 LLM 覆盖是否完整。
