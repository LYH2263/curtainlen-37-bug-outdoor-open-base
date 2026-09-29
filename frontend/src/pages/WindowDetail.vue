<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, putJSON } from '../api'
const props = defineProps({ id: String })
const w = ref(null); const types = ref([]); const err = ref(''); const msg = ref('')
async function load(){
  w.value = await getJSON(`/api/windows/${props.id}`)
}
onMounted(async () => {
  await load()
  types.value = (await getJSON('/api/exposure/types')).items
})
async function setType(value){
  err.value = ''; msg.value = ''
  try {
    w.value = await putJSON(`/api/windows/${props.id}/exposure`, { exposure_type: value })
    msg.value = '空间类型已更新（只影响之后新开的单）'
  } catch(e){ err.value = e.message; await load() }
}
</script>
<template><div class="page" v-if="w"><h1>{{ w.name }}</h1><p v-if="w.data_quality==='dirty'" class="bad">{{ w.note }}</p><p>宽 {{ w.width }} 高 {{ w.height }} 褶倍 {{ w.fullness }}</p>
<h2>空间类型</h2>
<p v-for="t in types" :key="t.value">
  <label><input type="radio" :name="'expo'+w.id" :value="t.value" :checked="w.exposure_type===t.value"
    :disabled="!t.enabled" @change="setType(t.value)">
    {{ t.label }}<template v-if="t.value!=='indoor'">（订货 = 基础 + {{ t.extra_meters ?? '?' }} m）</template></label>
</p>
<p v-if="msg" class="hint">{{ msg }}</p><p v-if="err" class="bad">{{ err }}</p>
</div></template>
