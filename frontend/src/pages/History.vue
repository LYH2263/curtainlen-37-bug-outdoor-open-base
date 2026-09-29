<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([]); const openId = ref(''); const detail = ref(null); const err = ref('')
onMounted(async () => { items.value = (await getJSON('/api/runs')).items })
async function open(id){
  err.value = ''; detail.value = null
  try { detail.value = await getJSON(`/api/runs/${id}`) } catch(e){ err.value = e.message }
}
// 列表/详情/户外摘要三路同源，全部钉住写入时的落库快照，不按现行设置重算。
function listOrder(r){ return r.result?.order_meters }
function detailOrder(d){ return d?.result?.order_meters }
function summaryOrder(d){ return d?.outdoor_summary?.order_meters }
</script>
<template><div class="page"><h1>记录</h1>
<p><input v-model="openId" placeholder="编号"> <button @click="open(openId)">打开</button></p>
<p v-if="err" class="bad">{{ err }}</p>
<div v-if="detail">
  <h2>#{{ detail.id }} <span class="tag">{{ detail.exposure?.label || detail.result?.exposure_type }}</span></h2>
  <p>基础 {{ detail.result?.meters }} m ｜ 加米 {{ detail.result?.extra_meters ?? 0 }} m ｜
     <b>详情订货 {{ detailOrder(detail) }} m</b> · 户外摘要订货 {{ summaryOrder(detail) }} m</p>
</div>
<ul><li v-for="r in items" :key="r.id">
  <a href="#" @click.prevent="open(r.id)">#{{ r.id }}</a>
  <span class="tag">{{ r.exposure?.label || r.result?.exposure_type }}</span>
  基础 {{ r.result?.meters }} m ｜ 加米 {{ r.result?.extra_meters ?? 0 }} m ｜
  列表订货 {{ listOrder(r) }} m · 户外摘要 {{ summaryOrder(r) }} m
</li></ul>
<p class="hint">类型、加米与订货米以写入时落库快照为准：之后改设置默认加米或把窗类型改室内再改回户外，旧编号不重算。</p>
</div></template>
