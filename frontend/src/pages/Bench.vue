<script setup>
import { onMounted, ref, watch } from 'vue'
import { getJSON, postJSON } from '../api'
import PanelCut from '../components/PanelCut.vue'
const windows = ref([]); const fabrics = ref([]); const wid = ref(1); const fid = ref(1)
const expoTypes = ref([]); const expo = ref('indoor'); const out = ref(null); const err = ref('')
onMounted(async () => {
  windows.value = (await getJSON('/api/windows')).items.filter(x=>x.data_quality==='clean')
  fabrics.value = (await getJSON('/api/fabrics')).items.filter(x=>x.data_quality==='clean')
  expoTypes.value = (await getJSON('/api/exposure/types')).items
  if (windows.value.length) wid.value = windows.value[0].id
  if (fabrics.value.length) fid.value = fabrics.value[0].id
  followWindowType()
})
// 算料台默认跟随窗上现行类型（只作新开单的初值，仍可手动改选）
function followWindowType(){
  const w = windows.value.find(x => x.id === Number(wid.value))
  if (w?.exposure_type) expo.value = w.exposure_type
}
watch(wid, followWindowType)
async function go(save){
  err.value = ''; out.value = null
  try {
    out.value = save
      ? await postJSON('/api/estimate',{window_id:wid.value,fabric_id:fid.value,save:true,exposure_type:expo.value})
      : await getJSON(`/api/estimate?window_id=${wid.value}&fabric_id=${fid.value}&exposure_type=${expo.value}`)
  } catch(e){ err.value = e.message }
}
</script>
<template><div class="page"><h1>算料</h1>
<select v-model.number="wid"><option v-for="x in windows" :key="x.id" :value="x.id">{{ x.name }}</option></select>
<select v-model.number="fid"><option v-for="x in fabrics" :key="x.id" :value="x.id">{{ x.name }}</option></select>
<select v-model="expo">
  <option v-for="t in expoTypes" :key="t.value" :value="t.value" :disabled="!t.enabled">
    {{ t.label }}<template v-if="t.value!=='indoor'">（+{{ t.extra_meters }}m<template v-if="!t.enabled">，已停用</template>）</template>
  </option>
</select>
<button @click="go(false)">干算</button><button @click="go(true)">保存订货</button>
<p v-if="err" class="bad">测算被拒绝：{{ err }}</p>
<template v-if="out">
<PanelCut :panels="out.panels" :cut-height="out.cut_height" :meters="out.meters" />
<p>曝晒类型：{{ out.exposure_label }} ｜ 类型 <b>{{ out.exposure_type }}</b> ｜ 基础 {{ out.meters }} m ＋ 加米 {{ out.extra_meters }} m ＝ <b>订货 {{ out.order_meters }} m</b></p>
<p class="hint" v-if="out.run_id">已写入编号 #{{ out.run_id }}；改设置或窗类型不会回刷该单。干算不落库、不影响已写入编号。</p>
</template>
</div></template>
