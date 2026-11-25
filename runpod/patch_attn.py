# Wan 2.2 ohne flash_attn: auf PyTorch-Attention ausweichen
p = '/workspace/Wan2.2/wan/modules/attention.py'
s = open(p).read()
marker = "    half_dtypes = (torch.float16, torch.bfloat16)"
add = """    if not FLASH_ATTN_2_AVAILABLE and not FLASH_ATTN_3_AVAILABLE:
        import torch.nn.functional as F
        o = F.scaled_dot_product_attention(q.transpose(1, 2).to(dtype), k.transpose(1, 2).to(dtype), v.transpose(1, 2).to(dtype), dropout_p=dropout_p)
        return o.transpose(1, 2).contiguous().type(q.dtype)
"""
i = s.index("def flash_attention(")
j = s.index(marker, i)
if "scaled_dot_product_attention(q.transpose(1, 2).to(dtype)" not in s:
    s = s[:j] + add + s[j:]
    open(p, 'w').write(s)
print('PATCHED')
