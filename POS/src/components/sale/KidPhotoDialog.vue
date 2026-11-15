<template>
	<Dialog v-model="show" :options="{ title: __('Kid Photo'), size: 'lg' }">
		<template #body-content>
			<div class="py-2">
				<p class="text-xs text-gray-600 mb-3">
					{{ hint || __("{0}: one photo per ticket ({1}). It is saved on the ticket after payment.", [item?.item_name || item?.item_code, slotCount]) }}
				</p>

				<!-- Live camera -->
				<div v-if="cameraSlot !== null" class="mb-3">
					<video
						ref="videoEl"
						autoplay
						playsinline
						muted
						class="w-full max-h-72 rounded-lg bg-black object-contain"
					></video>
					<div class="flex gap-2 mt-2">
						<Button class="flex-1" variant="subtle" @click="stopCamera">{{ __("Cancel") }}</Button>
						<Button class="flex-1" variant="solid" theme="blue" :loading="uploadingSlot !== null" @click="capture">
							{{ __("Capture") }}
						</Button>
					</div>
				</div>

				<div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
					<div
						v-for="(n, i) in slotCount"
						:key="i"
						class="border border-gray-200 rounded-lg p-2 flex flex-col items-center gap-2"
					>
						<div class="text-[11px] font-semibold text-gray-600">{{ __("Ticket {0}", [i + 1]) }}</div>
						<div class="w-24 h-24 rounded-lg bg-gray-100 border border-gray-200 overflow-hidden flex items-center justify-center">
							<img v-if="photos[i]" :src="photos[i]" class="w-full h-full object-cover" alt="kid" />
							<span v-else-if="uploadingSlot === i" class="text-[11px] text-gray-500">{{ __("Saving...") }}</span>
							<span v-else class="text-2xl text-gray-300">👤</span>
						</div>
						<div class="flex flex-wrap justify-center gap-1">
							<button
								type="button"
								class="h-7 px-2 text-[11px] font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
								:disabled="uploadingSlot !== null"
								@click="startCamera(i)"
							>
								{{ __("Camera") }}
							</button>
							<button
								type="button"
								class="h-7 px-2 text-[11px] font-semibold rounded-lg border border-blue-300 text-blue-700 hover:bg-blue-50 disabled:opacity-50"
								:disabled="uploadingSlot !== null"
								@click="pickFile(i)"
							>
								{{ __("Upload") }}
							</button>
							<button
								v-if="photos[i]"
								type="button"
								class="h-7 px-2 text-[11px] font-semibold rounded-lg text-red-600 hover:bg-red-50"
								@click="removePhoto(i)"
							>
								{{ __("Remove") }}
							</button>
						</div>
					</div>
				</div>
				<input ref="fileEl" type="file" accept="image/*" capture="environment" class="hidden" @change="onFilePicked" />
			</div>
		</template>
		<template #actions>
			<Button class="w-full" variant="solid" theme="blue" @click="show = false">{{ __("Done") }}</Button>
		</template>
	</Dialog>
</template>

<script setup>
import { Button, Dialog } from "frappe-ui"
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue"
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import { parseError } from "@/utils/errorHandler"

const props = defineProps({
	modelValue: Boolean,
	// Cart row (reactive store object); photos are kept on item.kid_photos.
	item: Object,
	// Optional text replacing the default "saved after payment" hint.
	hint: String,
})
const emit = defineEmits(["update:modelValue"])
const { showError } = useToast()

const show = computed({
	get: () => props.modelValue,
	set: (v) => emit("update:modelValue", v),
})

const MAX_SIDE = 800

const slotCount = computed(() => Math.max(1, Math.floor(Number(props.item?.quantity || props.item?.qty || 1))))
const photos = computed(() => props.item?.kid_photos || [])

const videoEl = ref(null)
const fileEl = ref(null)
const cameraSlot = ref(null)
const uploadingSlot = ref(null)
const fileSlot = ref(null)
let stream = null

function setPhoto(i, url) {
	if (!props.item) return
	const list = [...(props.item.kid_photos || [])]
	while (list.length < i) list.push("")
	list[i] = url
	props.item.kid_photos = list
}

function removePhoto(i) {
	setPhoto(i, "")
}

async function startCamera(i) {
	if (!navigator.mediaDevices?.getUserMedia) {
		// No camera API (e.g. plain http): fall back to the file picker.
		pickFile(i)
		return
	}
	try {
		stopCamera()
		stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
		cameraSlot.value = i
		await nextTick()
		if (videoEl.value) videoEl.value.srcObject = stream
	} catch (e) {
		console.error("Camera failed", e)
		showError(__("Could not open the camera"))
		stopCamera()
	}
}

function stopCamera() {
	if (stream) stream.getTracks().forEach((t) => t.stop())
	stream = null
	cameraSlot.value = null
}

function drawScaled(source, w, h) {
	const scale = Math.min(1, MAX_SIDE / Math.max(w, h))
	const canvas = document.createElement("canvas")
	canvas.width = Math.round(w * scale)
	canvas.height = Math.round(h * scale)
	canvas.getContext("2d").drawImage(source, 0, 0, canvas.width, canvas.height)
	return canvas.toDataURL("image/jpeg", 0.85)
}

async function capture() {
	const video = videoEl.value
	if (!video || !video.videoWidth) return
	const slot = cameraSlot.value
	const dataUrl = drawScaled(video, video.videoWidth, video.videoHeight)
	stopCamera()
	await upload(slot, dataUrl)
}

function pickFile(i) {
	fileSlot.value = i
	if (fileEl.value) {
		fileEl.value.value = ""
		fileEl.value.click()
	}
}

function onFilePicked(ev) {
	const file = ev.target.files?.[0]
	const slot = fileSlot.value
	if (!file || slot === null) return
	const reader = new FileReader()
	reader.onload = () => {
		const img = new Image()
		img.onload = () => upload(slot, drawScaled(img, img.naturalWidth, img.naturalHeight))
		img.onerror = () => showError(__("This file is not a valid image"))
		img.src = reader.result
	}
	reader.readAsDataURL(file)
}

async function upload(slot, dataUrl) {
	uploadingSlot.value = slot
	try {
		const res = await call("ecs_posnext.api.kid_photos.upload_kid_photo", { data_url: dataUrl })
		const url = (res?.message || res)?.file_url
		if (url) setPhoto(slot, url)
	} catch (e) {
		console.error("Kid photo upload failed", e)
		showError(parseError(e).message || __("Could not save the photo"))
	} finally {
		uploadingSlot.value = null
	}
}

watch(show, (v) => {
	if (!v) stopCamera()
})
onBeforeUnmount(stopCamera)
</script>
