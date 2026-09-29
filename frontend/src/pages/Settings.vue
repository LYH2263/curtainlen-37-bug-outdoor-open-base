<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, putJSON } from '../api'
const s = ref({}); const uvEnabled = ref(true); const uvExtra = ref('0.3'); const msg = ref(''); const err = ref('')
onMounted(async () => {
  s.value = await getJSON('/api/settings')
  uvEnabled.value = String(s.value.exposure_outdoor_uv_enabled ?? '1') !== '0'
  uvExtra.value = s.value.exposure_outdoor_uv_extra_m ?? '0.3'
})
async function save(){
  msg.value = ''; err.value = ''
  try {
    s.value = await putJSON('/api/settings', {
      exposure_outdoor_uv_enabled: uvEnabled.value ? '1' : '0',
      exposure_outdoor_uv_extra_m: String(uvExtra.value),
    })
    msg.value = '已保存'
  } catch(e){ err.value = e.message }
}
</script>
<template><div class="page"><h1>设置</h1>
<p>默认褶倍 {{ s.default_fullness }}</p>
<h2>空间曝晒</h2>
<p><label><input type="checkbox" v-model="uvEnabled"> 启用户外抗紫外（停用后新测算回到基础口径）</label></p>
<p><label>户外抗紫外固定加米（米）<input type="number" step="0.05" v-model="uvExtra"></label></p>
<button @click="save">保存</button>
<span v-if="msg">{{ msg }}</span><span v-if="err" class="bad">{{ err }}</span>
</div></template>
