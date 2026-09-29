<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([]); const openId = ref(''); const detail = ref(null); const err = ref('')
onMounted(async () => { items.value = (await getJSON('/api/runs')).items })
async function open(id){
  err.value = ''; detail.value = null
  try { detail.value = await getJSON(`/api/runs/${id}`) } catch(e){ err.value = e.message }
}
function listOrder(r){ return r.result?.list_order_meters_pin ?? r.outdoor_summary?.order_meters ?? r.result?.order_meters }
function detailOrder(d){ return d?.result?.order_meters }
function summaryOrder(d){ return d?.outdoor_summary?.order_meters ?? d?.exposure?.order_meters }
</script>
<template><div class="page"><h1>记录</h1>
<p><input v-model="openId" placeholder="编号"> <button @click="open(openId)">打开</button></p>
<p v-if="err" class="bad">{{ err }}</p>
<div v-if="detail">
  <h2>#{{ detail.id }} <span class="tag">{{ detail.exposure?.label || detail.result?.exposure_type }}</span></h2>
  <p>详情订货 {{ detailOrder(detail) }} m · 摘要订货 {{ summaryOrder(detail) }} m
    <template v-if="detail.result?.extra_meters!=null">（基础 {{ detail.result?.meters }} + 加米 {{ detail.result?.extra_meters }}）</template>
  </p>
</div>
<ul><li v-for="r in items" :key="r.id">
  <a href="#" @click.prevent="open(r.id)">#{{ r.id }}</a>
  <span class="tag">{{ r.exposure?.label || r.result?.exposure_type }}</span>
  列表订货 {{ listOrder(r) }} m · 摘要 {{ r.outdoor_summary?.order_meters }} m
  <template v-if="r.result?.extra_meters">（加米 {{ r.result.extra_meters }}）</template>
</li></ul>
<p class="hint">列表 / 详情 / 户外摘要可能各算各的。改设置默认加米或把窗类型改室内再改回户外后再打开旧单。</p>
</div></template>
