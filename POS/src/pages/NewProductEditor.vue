<template>
	<div class="min-h-screen bg-gray-50 flex flex-col" dir="rtl">

		<!-- ===== LIST MODE ===== -->
		<template v-if="mode==='list'">
			<!-- Header -->
			<div class="bg-[#f4f6fb] px-5 sm:px-8 pt-6 pb-2 flex items-center justify-between">
				<div class="flex items-center gap-3">
					<button @click="goBack" class="p-2 rounded-lg hover:bg-gray-200 transition-colors">
						<svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
					</button>
					<h1 class="text-2xl font-bold text-[#1a1a2e] tracking-tight">{{ __('Item Manager') }}</h1>
				</div>
				<button @click="router.push({ name: 'NewProductEditor', params: { itemId: 'new' } })" class="px-5 py-2.5 rounded-lg bg-[#1a1a2e] text-white text-sm font-semibold hover:bg-[#2d2d4e] flex items-center gap-2 shadow-sm">
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
					{{ __('+ Add New Item') }}
				</button>
			</div>

			<main class="flex-1 overflow-y-auto px-5 sm:px-8 pb-6 bg-[#f4f6fb]">
				<!-- Card Wrapper -->
				<div class="bg-white rounded-xl border border-[#e0e6f0] shadow-sm p-5 mt-2">
					<!-- Search & Filters Row -->
					<div class="flex flex-col sm:flex-row items-start sm:items-center gap-3 mb-5">
						<div class="relative flex-1 max-w-sm">
							<svg class="w-4 h-4 text-gray-400 absolute top-1/2 -translate-y-1/2 start-3 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
							<input v-model="listSearch" @input="onListSearch" :placeholder="__('Search')" class="w-full bg-[#f4f6fb] border-none rounded-full ps-10 pe-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 placeholder-gray-400"/>
						</div>
						<div class="flex items-center gap-2 ms-auto">
							<div class="relative">
								<svg class="w-3.5 h-3.5 text-gray-400 absolute top-1/2 -translate-y-1/2 start-2.5 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"/></svg>
								<select v-model="listFilterGroup" @change="refreshList" class="appearance-none border border-gray-300 rounded-lg ps-8 pe-8 py-1.5 text-xs bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer">
									<option value="">{{ __('Item Group') }}</option>
									<option v-for="c in categories" :key="c.name" :value="c.name">{{ c.name }}</option>
								</select>
							</div>
							<div class="relative">
								<svg class="w-3.5 h-3.5 text-gray-400 absolute top-1/2 -translate-y-1/2 start-2.5 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
								<select v-model="listFilterClassification" @change="refreshList" class="appearance-none border border-gray-300 rounded-lg ps-8 pe-8 py-1.5 text-xs bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer">
									<option value="">{{ __('Classification') }}</option>
									<option v-for="cl in classifications" :key="cl.name" :value="cl.name">{{ cl.name }}</option>
								</select>
							</div>
							<div class="relative">
								<svg class="w-3.5 h-3.5 text-gray-400 absolute top-1/2 -translate-y-1/2 start-2.5 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18"/></svg>
								<select v-model="listFilterType" @change="refreshList" class="appearance-none border border-gray-300 rounded-lg ps-8 pe-8 py-1.5 text-xs bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer">
									<option value="">{{ __('Type') }}</option>
									<option value="normal">{{ __('Normal') }}</option>
									<option value="template">{{ __('Template') }}</option>
									<option value="variant">{{ __('Variant') }}</option>
									<option value="bundle">{{ __('Bundle') }}</option>
								</select>
							</div>
							<button @click="refreshList" :disabled="listLoading" class="flex items-center gap-1.5 border border-gray-300 rounded-lg px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-50 disabled:opacity-40">
								<svg :class="['w-3.5 h-3.5',listLoading?'animate-spin':'']" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
								{{ __('Refresh') }}
							</button>
						</div>
					</div>

					<!-- Loading -->
					<div v-if="listLoading" class="py-16 text-center"><div class="inline-block w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div></div>

					<!-- Data Table -->
					<div v-else-if="listItems.length>0" class="overflow-x-auto">
						<table class="w-full text-sm">
							<thead>
								<tr class="border-b border-[#e0e6f0]">
									<th class="tbl-th w-[50px]"></th>
									<th class="tbl-th text-start">{{ __('ITEM CODE') }}</th>
									<th class="tbl-th text-start" style="min-width:220px">{{ __('ITEM NAME') }}</th>
									<th class="tbl-th text-start">{{ __('GROUP') }}</th>
									<th class="tbl-th text-start">{{ __('CLASSIFICATION') }}</th>
									<th class="tbl-th text-end">{{ __('PRICE') }}</th>
									<th class="tbl-th text-center">{{ __('TYPE') }}</th>
									<th class="tbl-th text-center" style="width:120px">{{ __('ACTIONS') }}</th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="item in listItems" :key="item.name" class="border-b border-[#f0f2f8] hover:bg-[#f0f4ff] transition-colors">
									<!-- Image -->
									<td class="tbl-td">
										<div class="w-9 h-9 rounded-full bg-[#f4f6fb] flex items-center justify-center overflow-hidden">
											<img v-if="item.image" :src="item.image" class="w-full h-full object-cover"/>
											<svg v-else class="w-4 h-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
										</div>
									</td>
									<!-- Item Code -->
									<td class="tbl-td text-gray-600">{{ item.item_code }}</td>
									<!-- Item Name -->
									<td class="tbl-td">
										<div class="font-medium text-[#1a1a2e]">{{ item.item_name }}</div>
										<div v-if="item.custom_item_name_arabic" class="text-xs text-[#8a94a6] mt-0.5">{{ item.custom_item_name_arabic }}</div>
									</td>
									<!-- Group -->
									<td class="tbl-td text-gray-600">{{ item.item_group }}</td>
									<!-- Classification -->
									<td class="tbl-td text-gray-600">{{ item.custom_item_classification || '' }}</td>
									<!-- Price -->
									<td class="tbl-td text-end font-medium">{{ formatCurrency(item.standard_rate) }}</td>
									<!-- Type -->
									<td class="tbl-td text-center">
										<span v-if="item.has_variants" class="inline-block px-2.5 py-0.5 rounded text-[11px] font-medium bg-amber-50 text-amber-700">{{ __('Template') }}</span>
										<span v-else-if="item.variant_of" class="inline-block px-2.5 py-0.5 rounded text-[11px] font-medium bg-blue-50 text-blue-700">{{ __('Variant') }}</span>
										<span v-else-if="item.enabled_item_bundle" class="inline-block px-2.5 py-0.5 rounded text-[11px] font-medium bg-purple-50 text-purple-700">{{ __('Bundle') }}</span>
										<span v-else class="inline-block px-2.5 py-0.5 rounded text-[11px] font-medium bg-gray-100 text-[#8a94a6]">{{ __('Normal') }}</span>
									</td>
									<!-- Actions -->
									<td class="tbl-td text-center">
										<div class="flex items-center justify-center gap-0.5">
											<button @click="router.push({ name: 'NewProductEditor', params: { itemId: item.item_code || item.name } })" class="p-1.5 rounded hover:bg-gray-100 text-[#8a94a6] hover:text-[#3a3a4a] transition-colors" :title="__('Edit')">
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
											</button>
											<button @click="duplicateItem(item)" class="p-1.5 rounded hover:bg-gray-100 text-[#8a94a6] hover:text-[#3a3a4a] transition-colors" :title="__('Duplicate')">
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
											</button>
										</div>
									</td>
								</tr>
							</tbody>
						</table>
					</div>
					<div v-else class="py-16 text-center text-sm text-gray-400">{{ __('لا توجد أصناف') }}</div>

					<!-- Pagination -->
					<div v-if="listTotal>listPageLength" class="flex items-center justify-between mt-4 pt-3 border-t border-[#e0e6f0] text-xs text-gray-500">
						<span>{{ listStart+1 }}-{{ Math.min(listStart+listPageLength, listTotal) }} {{ __('من') }} {{ listTotal }}</span>
						<div class="flex gap-2">
							<button @click="listStart=Math.max(0,listStart-listPageLength);loadListItems()" :disabled="listStart===0" class="px-3 py-1.5 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-40">{{ __('السابق') }}</button>
							<button @click="listStart+=listPageLength;loadListItems()" :disabled="listStart+listPageLength>=listTotal" class="px-3 py-1.5 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-40">{{ __('التالي') }}</button>
						</div>
					</div>
				</div>
			</main>
		</template>

		<!-- ===== EDITOR MODE ===== -->
		<template v-else>
		<header class="bg-slate-800 px-4 sm:px-7 py-3 flex items-center gap-4 sticky top-0 z-30">
			<button @click="goBackToList" class="p-2 rounded-lg hover:bg-slate-700 transition-colors flex-shrink-0">
				<svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
			</button>
			<div class="flex-1 min-w-0 overflow-hidden">
				<h1 class="text-base sm:text-xl font-bold text-white truncate">{{ isEditing ? product.item_name : __('إضافة صنف جديد') }}</h1>
				<p class="text-[10px] sm:text-xs text-slate-300 truncate">{{ productTypeLabel }}</p>
			</div>
			<button @click="saveProduct" :disabled="saving || !canSave" class="px-5 py-2 rounded-xl bg-white text-slate-800 text-sm font-bold hover:bg-gray-100 disabled:opacity-50 flex items-center gap-2 flex-shrink-0 shadow-sm transition-all active:scale-95">
				<svg v-if="saving" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
				<span v-else>{{ __('حفظ') }}</span>
			</button>
		</header>

		<div v-if="loading" class="h-1 bg-blue-100"><div class="h-full bg-blue-500 animate-pulse w-full"></div></div>
		<div v-if="savingInBackground" class="px-4 py-2 bg-amber-600 text-white text-sm font-medium flex items-center gap-2">
			<svg class="animate-spin w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
			{{ __('جارٍ حفظ المتغيرات في الخلفية… يرجى الانتظار') }}
		</div>

		<main v-if="!loading" class="flex-1 overflow-y-auto">
			<div class="grid grid-cols-1 md:grid-cols-12 min-h-[calc(100vh-64px)]">
				<!-- PANEL 1: Basic Info (3/12) -->
				<div class="md:col-span-3 bg-gray-50 p-4 sm:p-6 border-s border-gray-200 overflow-y-auto">
					<div class="text-sm font-bold text-slate-800 mb-5 pb-2 border-b-2 border-gray-200">{{ __('المعلومات الأساسية') }}</div>
					<div class="mb-4">
						<label class="form-lbl">{{ __('نوع الصنف') }}</label>
						<div class="flex mt-1 rounded-lg border border-gray-300 overflow-hidden">
							<button @click="product.product_type='standard'" :class="['flex-1 py-2 text-xs font-medium',product.product_type==='standard'?'bg-blue-50 text-blue-700':'bg-white text-gray-600']">{{ __('وجبة عادية') }}</button>
							<button @click="product.product_type='combo'" :class="['flex-1 py-2 text-xs font-medium border-s border-gray-300',product.product_type==='combo'?'bg-purple-50 text-purple-700':'bg-white text-gray-600']">{{ __('كومبو') }}</button>
						</div>
					</div>
					<div class="mb-4"><label class="form-lbl">{{ __('اسم الصنف بالعربي') }} *</label><input v-model="product.custom_item_name_arabic" type="text" :placeholder="__('مثال: برجر دجاج')" class="form-input"/></div>
					<div class="mb-4"><label class="form-lbl">{{ __('اسم الصنف بالانجليزي') }} *</label><input v-model="product.item_name" type="text" placeholder="ex: Chicken Burger" class="form-input" dir="ltr"/></div>
					<div class="mb-4" v-if="!isEditing"><label class="form-lbl">{{ __('كود الصنف') }} *</label><input v-model="product.item_code" type="text" placeholder="ex: BURGER-001" class="form-input" dir="ltr"/></div>
					<div class="mb-4"><label class="form-lbl">{{ __('الفئة') }} *</label><select v-model="product.item_group" class="form-input"><option value="">{{ __('اختر الفئة') }}</option><option v-for="c in categories" :key="c.name" :value="c.name">{{ c.name }}</option></select></div>
					<div class="mb-4 space-y-2" dir="ltr">
						<label class="flex items-center gap-2 cursor-pointer"><input v-model="product.custom_is_pos_item" type="checkbox" class="toggle-cb"/><span class="text-xs text-gray-700">{{ __('إظهار في الـ POS') }}</span></label>
						<label class="flex items-center gap-2 cursor-pointer"><input v-model="product.custom_fast_sell" type="checkbox" class="toggle-cb"/><span class="text-xs text-gray-700">{{ __('بيع سريع') }}</span></label>
					</div>
					<div class="mb-4">
						<div class="flex items-center justify-between mb-2"><label class="form-lbl mb-0">{{ __('الأسعار') }}</label><button @click="addPriceRow" class="p-1 rounded text-blue-600 hover:bg-blue-50"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg></button></div>
						<div v-if="itemPrices.length===0" class="text-xs text-gray-400 py-2">{{ __('اضغط + لإضافة سعر') }}</div>
						<div v-for="(pi,idx) in itemPrices" :key="idx" class="flex items-center gap-2 mb-2">
							<button @click="itemPrices.splice(idx,1)" class="w-5 h-5 flex-shrink-0 rounded bg-red-500 text-white flex items-center justify-center hover:bg-red-600 transition-colors">
								<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
							</button>
							<select v-model="pi.price_list" class="form-input flex-1 !py-1.5 text-xs min-w-[140px]"><option value="">{{ __('قائمة الأسعار') }}</option><option v-for="pl in priceLists" :key="pl.name" :value="pl.name">{{ pl.name }}</option></select>
							<input v-model.number="pi.price" type="number" min="0" class="form-input !py-1.5 text-xs !w-24 flex-shrink-0" dir="ltr"/>
							<span class="text-[10px] text-gray-400 flex-shrink-0">EGP</span>
							</div>
					</div>
				</div>

				<!-- PANEL 2: Variants OR Combo (6/12) -->
				<div v-if="product.product_type==='standard'" class="md:col-span-6 bg-white p-4 sm:p-6 border-s border-gray-200 overflow-y-auto">
					<div class="flex items-center justify-between mb-5 pb-2 border-b-2 border-gray-200">
						<span class="text-sm font-bold text-slate-800">{{ __('Variants') }}</span>
						<label class="flex items-center gap-2" dir="ltr"><input v-model="hasVariants" type="checkbox" class="toggle-cb"/></label>
					</div>
					<template v-if="hasVariants">
						<!-- Attributes -->
						<div class="rounded-xl border border-gray-200 mb-4">
							<div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 text-xs font-semibold text-slate-800"><span>{{ __('الخصائص') }}</span><button @click="showAddAttributeDialog=true" class="p-1 rounded text-blue-600 hover:bg-blue-50"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg></button></div>
							<div class="p-3">
								<div v-if="product.attributes.length===0" class="text-center text-xs text-gray-400 py-4">{{ __('لا توجد خصائص') }}</div>
								<div v-for="(attr,idx) in product.attributes" :key="attr.attribute" class="bg-gray-50 rounded-lg border border-gray-200 p-3 mb-2">
									<div class="flex items-center gap-2"><span class="w-5 h-5 rounded-full bg-blue-500 text-white text-[10px] flex items-center justify-center font-bold">{{ idx+1 }}</span><strong class="text-xs">{{ attr.attribute }}</strong><button @click="removeAttribute(attr)" class="ms-auto p-1 text-red-500 hover:bg-red-50 rounded"><svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button></div>
									<div class="mt-2 flex flex-wrap gap-1"><span v-for="val in attr.values" :key="val" class="px-2 py-0.5 rounded-full border border-gray-300 text-[10px] text-gray-600">{{ val }}</span></div>
								</div>
							</div>
						</div>
						<!-- Combinations Counter -->
						<div v-if="product.attributes.length >= 2 && expectedVariantsCount > 0" class="bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 mb-4 flex items-center gap-2 text-xs text-blue-700">
							<svg class="w-4 h-4 text-blue-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
							{{ __('سيتم توليد') }} {{ expectedVariantsCount }} {{ __('variant من combinations الخصائص') }}
						</div>
						<!-- Variants List -->
						<div class="rounded-xl border border-gray-200 mb-4">
							<div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 text-xs font-semibold text-slate-800">
								<div class="flex items-center gap-2">
									<span>{{ __('المتغيرات') }}</span>
									<span v-if="product.variants.length" class="bg-gray-100 text-gray-500 text-[10px] font-medium px-1.5 py-0.5 rounded-full">{{ product.variants.length }}</span>
								</div>
								<button @click="generateAllVariants" :disabled="product.attributes.length===0" class="px-2 py-1 rounded text-xs text-blue-600 hover:bg-blue-50 disabled:opacity-40" :title="isEditing ? __('يضيف المتغيرات الناقصة فقط') : ''">{{ isEditing ? __('توليد الناقص') : __('توليد تلقائي') }}</button>
							</div>
							<div class="p-2">
								<div v-if="product.variants.length===0" class="text-center text-xs text-gray-400 py-6">{{ __('أضف الخصائص ثم اضغط توليد تلقائي') }}</div>

								<!-- Nested attribute tree -->
								<template v-if="product.variants.length > 0">
									<div v-for="(row, idx) in flatVariantTree" :key="idx">

										<!-- ── Group header ── -->
										<div v-if="row.type==='group'"
											@click="toggleGroup(row.key)"
											:style="`margin-inline-start: ${row.level * 16}px`"
											:class="['flex items-center gap-2 px-2 py-1.5 rounded-lg cursor-pointer select-none mt-1.5 mb-0.5 border',
												row.level===0 ? 'bg-[#1a1a2e]/5 border-[#1a1a2e]/10' :
												row.level===1 ? 'bg-blue-50/60 border-blue-100' :
												'bg-gray-50 border-gray-100']"
										>
											<svg :class="['w-3 h-3 flex-shrink-0 text-gray-400 transition-transform duration-150', row.collapsed ? '-rotate-90' : '']" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7"/></svg>
											<span :class="['text-[10px] font-semibold px-1.5 py-0.5 rounded-full leading-none',
												row.level===0 ? 'bg-[#1a1a2e] text-white' :
												row.level===1 ? 'bg-blue-500 text-white' :
												'bg-gray-400 text-white']">{{ row.attr }}</span>
											<span :class="['text-xs font-semibold truncate',
												row.level===0 ? 'text-[#1a1a2e]' :
												row.level===1 ? 'text-blue-800' :
												'text-gray-700']">{{ row.label }}</span>
											<span class="ms-auto text-[10px] text-gray-400 bg-white border border-gray-200 rounded-full px-1.5 leading-5 flex-shrink-0">{{ row.count }}</span>
										</div>

										<!-- ── Leaf variant row ── -->
										<div v-else-if="row.type==='leaf'"
											:style="`margin-inline-start: ${row.level * 16}px`"
											:class="['flex items-center gap-2 bg-white rounded-lg border border-gray-200 px-2.5 py-2 mb-0.5 hover:border-blue-200 hover:bg-blue-50/30 transition-colors', row.variant.disabled ? 'opacity-50' : '']"
										>
											<!-- Attribute chip + value -->
											<div class="flex-1 min-w-0 flex items-center gap-1.5">
												<span class="text-[9px] font-semibold bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded-full flex-shrink-0 whitespace-nowrap">{{ row.attrName }}</span>
												<span class="text-xs font-medium text-gray-800 truncate">{{ row.label }}</span>
											</div>
											<!-- New variant: code input -->
											<input v-if="!row.variant.isExisting" v-model="row.variant.item_code" class="form-input !py-1 text-xs w-24 flex-shrink-0" dir="ltr" :placeholder="__('الكود')"/>
											<!-- Price -->
											<div class="flex items-center gap-1 flex-shrink-0">
												<input v-model.number="row.variant.price" type="number" min="0"
													class="w-20 text-center text-xs font-semibold border border-gray-200 rounded-lg px-2 py-1 focus:ring-2 focus:ring-blue-400 outline-none bg-gray-50"
													dir="ltr" placeholder="0" @input="row.variant.prices=[]"/>
												<span class="text-[10px] text-gray-400">EGP</span>
											</div>
											<!-- Actions -->
											<div class="flex items-center gap-0.5 flex-shrink-0">
												<button @click="openVariantPricesDialog(row.variant)" class="p-1.5 rounded-lg hover:bg-green-50 text-green-600" :title="__('الأسعار')">
													<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
												</button>
												<button @click="openRecipeDialog(row.variant)" :disabled="!row.variant.item_code" class="p-1.5 rounded-lg hover:bg-blue-50 text-blue-500 disabled:opacity-30" :title="__('الوصفة')">
													<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/></svg>
												</button>
												<button @click="row.variant.show_bundle=!row.variant.show_bundle"
													:class="['p-1.5 rounded-lg', row.variant.show_bundle ? 'text-amber-500 bg-amber-50' : 'text-gray-300 hover:text-gray-500 hover:bg-gray-100']"
													:title="__('عرض في POS')">
													<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
												</button>
												<!-- Disable / enable existing variant -->
											<button v-if="row.variant.isExisting" @click="row.variant.disabled = !row.variant.disabled"
												:class="['p-1.5 rounded-lg', row.variant.disabled ? 'text-red-500 bg-red-50' : 'text-gray-300 hover:text-gray-500 hover:bg-gray-100']"
												:title="row.variant.disabled ? __('معطّل — اضغط للتفعيل') : __('مفعّل — اضغط للتعطيل')">
												<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 5.636a9 9 0 11-12.728 0M12 3v9"/></svg>
											</button>
											<button v-if="!row.variant.isExisting" @click="removeVariantByName(row.variant.name)" class="p-1.5 rounded-lg hover:bg-red-50 text-red-400 hover:text-red-600" :title="__('حذف')">
													<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
												</button>
											</div>
										</div>

									</div>
								</template>

								<button @click="addVariantManually" class="mt-3 w-full py-1.5 border border-dashed border-gray-300 rounded-lg text-xs text-gray-500 hover:text-blue-600 hover:border-blue-300 transition-colors">+ {{ __('إضافة متغير') }}</button>
							</div>
						</div>
						<!-- Addons -->
						<div class="rounded-xl border border-gray-200">
							<div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 text-xs font-semibold text-slate-800"><span>{{ __('الإضافات') }}</span><button @click="showAddAddonDialog=true" class="p-1 rounded text-blue-600 hover:bg-blue-50"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg></button></div>
							<div class="p-3">
								<input v-model="product.addons_label" type="text" :placeholder="__('عنوان الإضافات')" class="form-input text-xs mb-3"/>
								<div v-if="product.addons.length===0" class="text-center text-xs text-gray-400 py-3">{{ __('لا توجد إضافات') }}</div>
								<div v-for="(a,idx) in product.addons" :key="idx" class="bg-gray-50 rounded-lg border border-gray-200 p-2 mb-2 space-y-2">
									<div class="flex items-center gap-2">
										<span class="text-xs font-semibold flex-1">{{ a.item_name||a.item_code }}</span>
										<div class="flex items-center gap-1">
											<input v-model.number="a.price" type="number" min="0" class="form-input !py-1 text-[10px] !w-16" dir="ltr"/>
											<span class="text-[8px] text-gray-400">EGP</span>
										</div>
										<button @click="product.addons.splice(idx,1)" class="p-1 text-red-500 hover:bg-red-50 rounded transition-colors"><svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
									</div>
									<div class="flex items-center gap-2">
										<select v-model="a.applicable_attribute" class="form-input !py-0.5 text-[9px] flex-1">
											<option value="">{{ __('كل الأحجام') }}</option>
											<option v-for="at in product.attributes" :key="at.attribute" :value="at.attribute">{{ at.attribute }}</option>
										</select>
										<select v-if="a.applicable_attribute" v-model="a.applicable_value" class="form-input !py-0.5 text-[9px] flex-1">
											<option value="">{{ __('كل القيم') }}</option>
											<option v-for="av in (product.attributes.find(at => at.attribute === a.applicable_attribute)?.values || [])" :key="av" :value="av">{{ av }}</option>
										</select>
									</div>
								</div>
							</div>
						</div>
					</template>
					<div v-else class="text-center text-gray-400 py-10 text-xs">{{ __('فعّل الـ Variants لإضافة أحجام وأنواع') }}</div>
				</div>

				<!-- PANEL 2 ALT: Combo (6/12) -->
				<div v-if="product.product_type==='combo'" class="md:col-span-6 bg-white border-s border-gray-200 overflow-y-auto flex flex-col">
					<div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between flex-shrink-0">
						<div>
							<div class="text-sm font-bold text-slate-800">{{ __('أقسام الوجبة') }}</div>
							<div class="text-[11px] text-gray-400 mt-0.5">{{ __('كل قسم = خيار للعميل عند الطلب') }}</div>
						</div>
						<span class="bg-gray-100 text-gray-500 text-[10px] font-semibold px-2 py-1 rounded-full">{{ product.sections.length }} {{ __('قسم') }}</span>
					</div>

					<div class="flex-1 overflow-y-auto p-4 space-y-3">
						<div v-for="(sec,si) in product.sections" :key="si"
							class="rounded-xl border border-gray-200 overflow-hidden shadow-sm">

							<!-- Section header -->
							<div class="bg-[#f8f9fc] px-3 py-2.5 flex items-center gap-2 border-b border-gray-200">
								<div class="w-6 h-6 rounded-lg bg-[#1a1a2e] text-white text-[10px] font-bold flex items-center justify-center flex-shrink-0">{{ si+1 }}</div>
								<input v-model="sec.name" :placeholder="__('اسم القسم، مثال: اختر الحجم')"
									class="flex-1 bg-transparent text-sm font-semibold text-slate-800 outline-none placeholder-gray-300 min-w-0"/>
								<button @click="product.sections.splice(si,1)" class="p-1 rounded-lg hover:bg-red-50 text-gray-300 hover:text-red-500 flex-shrink-0">
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
								</button>
							</div>

							<!-- Section settings -->
							<div class="px-3 py-2 flex flex-wrap items-center gap-2 border-b border-gray-100 bg-white">
								<label class="flex items-center gap-1.5 text-xs text-gray-600 cursor-pointer">
									<input v-model="sec.is_required" type="checkbox" class="toggle-cb"/>
									<span class="font-medium">{{ __('إلزامي') }}</span>
								</label>
								<div class="flex items-center gap-1 text-xs text-gray-500 ms-auto">
									<span>{{ __('الحد الأدنى') }}</span>
									<input v-model.number="sec.min_qty" type="number" min="0" class="w-12 text-center border border-gray-200 rounded-lg px-1 py-0.5 text-xs outline-none focus:ring-1 focus:ring-blue-400" dir="ltr"/>
									<span>{{ __('الأقصى') }}</span>
									<input v-model.number="sec.max_qty" type="number" min="1" class="w-12 text-center border border-gray-200 rounded-lg px-1 py-0.5 text-xs outline-none focus:ring-1 focus:ring-blue-400" dir="ltr"/>
								</div>
							</div>

							<!-- Options list -->
							<div class="p-3 space-y-2">
								<div v-if="sec.options.length===0" class="text-center text-[11px] text-gray-400 py-3">{{ __('اضغط + لإضافة الأصناف المتاحة في هذا القسم') }}</div>

								<div v-for="(opt,oi) in sec.options" :key="oi">
									<!-- Option row -->
									<div :class="['flex items-center gap-2 rounded-lg px-3 py-2 border',
										opt.has_variants ? 'bg-indigo-50 border-indigo-200' : 'bg-white border-gray-200 hover:border-blue-200']">

										<!-- Default checkbox -->
										<label v-if="!opt.has_variants" class="flex-shrink-0 cursor-pointer" :title="__('افتراضي')">
											<input v-model="opt.default_selected" type="checkbox" class="toggle-cb"/>
										</label>

										<!-- Expand toggle for variant group -->
										<button v-if="opt.has_variants" @click="opt.expanded=!opt.expanded"
											:class="['p-1 rounded-lg flex-shrink-0', opt.expanded ? 'bg-indigo-200 text-indigo-800' : 'bg-indigo-100 text-indigo-600']">
											<svg :class="['w-3.5 h-3.5 transition-transform', opt.expanded ? 'rotate-180' : '']" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7"/></svg>
										</button>

										<!-- Item search -->
										<div class="flex-1 min-w-0">
											<input :value="opt.item_name||opt.item_code"
												@focus="startOptionSearch($event,opt,si,oi)"
												@input="onOptionSearchInput($event,opt,si,oi)"
												@blur="window.setTimeout(()=>{ activeOptionSearch=null; optionSearchResults=[] },200)"
												:placeholder="__('ابحث عن صنف...')"
												:class="['w-full text-xs outline-none bg-transparent placeholder-gray-400 font-medium',
													opt.item_code ? 'text-slate-800' : 'text-gray-400']"/>
										</div>

										<!-- Qty + Extra price (non-variant) -->
										<template v-if="!opt.has_variants">
											<div class="flex items-center gap-1 flex-shrink-0">
												<input v-model.number="opt.qty" type="number" min="1"
													class="w-10 text-center text-xs border border-gray-200 rounded-lg px-1 py-1 outline-none focus:ring-1 focus:ring-blue-400 bg-gray-50"
													dir="ltr" :title="__('الكمية')"/>
												<span class="text-[10px] text-gray-400">×</span>
											</div>
											<div class="flex items-center gap-1 flex-shrink-0">
												<span class="text-[10px] text-gray-400">+</span>
												<input v-model.number="opt.extra_price" type="number" min="0"
													class="w-16 text-center text-xs border border-gray-200 rounded-lg px-1 py-1 outline-none focus:ring-1 focus:ring-blue-400 font-semibold text-blue-600 bg-gray-50"
													dir="ltr"/>
												<button @click="openExtraPricesDialog(opt)" class="p-1 rounded-lg hover:bg-green-50 text-gray-300 hover:text-green-600" :title="__('أسعار متعددة')">
													<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
												</button>
											</div>
										</template>

										<!-- Global qty + price for variant group -->
										<template v-if="opt.has_variants">
											<div class="flex items-center gap-1 flex-shrink-0">
												<input v-model.number="opt.qty" type="number" min="1"
													class="w-10 text-center text-xs border border-indigo-200 rounded-lg px-1 py-1 outline-none focus:ring-1 focus:ring-indigo-400 bg-indigo-50 text-indigo-700"
													dir="ltr" :title="__('الكمية المسموح بها')"/>
												<span class="text-[10px] text-indigo-400">×</span>
											</div>
											<div class="flex items-center gap-1 flex-shrink-0">
												<span class="text-[10px] text-indigo-400">+</span>
												<input v-model.number="opt.global_price" type="number" min="0"
													@input="applyGlobalPrice(opt)"
													class="w-16 text-center text-xs border border-indigo-200 rounded-lg px-1 py-1 outline-none focus:ring-1 focus:ring-indigo-400 font-semibold text-indigo-700 bg-indigo-50"
													dir="ltr" :placeholder="__('سعر')"/>
											</div>
										</template>

										<button @click="sec.options.splice(oi,1)" class="p-1 rounded-lg hover:bg-red-50 text-gray-300 hover:text-red-500 flex-shrink-0">
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
										</button>
									</div>

									<!-- Expanded variants sub-list -->
									<div v-if="opt.has_variants&&opt.variants&&opt.expanded"
										class="ms-8 mt-1 rounded-xl border border-indigo-100 bg-white overflow-hidden">
										<div class="px-3 py-1.5 bg-indigo-50 border-b border-indigo-100 text-[10px] font-semibold text-indigo-600 flex items-center justify-between">
											<span>{{ opt.variants.length }} {{ __('variant') }}</span>
											<button @click="openAddVariantDialog(opt)" class="text-indigo-600 hover:underline">+ {{ __('إضافة') }}</button>
										</div>

										<!-- Lock Group header hint -->
										<div class="px-3 py-1.5 bg-amber-50 border-b border-amber-100">
											<p class="text-[10px] text-amber-700 font-semibold">🔒 {{ __('مجموعة القيد — اكتب نفس الكلمة للأصناف التي تتوافق مع بعض (مثال: ريجيولار / سبايسي)') }}</p>
										</div>
										<div v-for="(vr,vi) in opt.variants" :key="vi"
											class="flex items-center gap-2 px-3 py-2 border-b border-gray-50 last:border-0 hover:bg-gray-50">
											<label class="flex-shrink-0 cursor-pointer" :title="__('افتراضي')">
												<input v-model="vr.default_selected" type="checkbox" class="toggle-cb"/>
											</label>
											<span class="text-xs text-slate-700 font-medium flex-1 truncate min-w-0">{{ vr.item_name }}</span>
											<!-- Lock group tag -->
											<input v-model="vr.lock_group" type="text"
												class="w-20 text-center text-[10px] border border-amber-200 rounded px-1 py-0.5 outline-none focus:ring-1 focus:ring-amber-400 bg-amber-50 text-amber-800 placeholder-amber-300"
												:placeholder="__('مجموعة')" :title="__('مجموعة القيد')" dir="rtl"/>
											<div class="flex items-center gap-1 flex-shrink-0">
												<input v-model.number="vr.qty" type="number" min="1"
													class="w-10 text-center text-[10px] border border-gray-200 rounded px-1 py-0.5 outline-none focus:ring-1 focus:ring-blue-400 bg-gray-50"
													dir="ltr" :title="__('الكمية')"/>
												<span class="text-[10px] text-gray-400">×</span>
												<span class="text-[10px] text-gray-400">+</span>
												<input v-model.number="vr.extra_price" type="number" min="0"
													class="w-14 text-center text-[10px] border border-gray-200 rounded px-1 py-0.5 outline-none font-semibold text-blue-600 bg-gray-50"
													dir="ltr"/>
												<button @click="openExtraPricesDialog(vr)" class="p-1 rounded hover:bg-green-50 text-gray-300 hover:text-green-600" :title="__('أسعار متعددة')">
													<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
												</button>
											</div>
											<button @click="opt.variants.splice(vi,1);if(!opt.variants.length)opt.has_variants=false"
												class="p-1 rounded hover:bg-red-50 text-gray-300 hover:text-red-500 flex-shrink-0">
												<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
											</button>
										</div>
									</div>
								</div>

								<!-- Add option button -->
								<button @click="sec.options.push({item_code:'',item_name:'',extra_price:0,default_selected:false,qty:1,expanded:false})"
									class="w-full py-1.5 border border-dashed border-gray-200 rounded-lg text-xs text-gray-400 hover:text-blue-600 hover:border-blue-300 transition-colors mt-1">
									+ {{ __('إضافة صنف للقسم') }}
								</button>
							</div>
						</div>

						<!-- Add section button -->
						<button @click="product.sections.push({name:'',section_type:'Component',is_required:false,min_qty:0,max_qty:1,options:[]})"
							class="w-full py-3 border-2 border-dashed border-gray-200 rounded-xl text-xs font-semibold text-gray-400 hover:text-blue-600 hover:border-blue-300 transition-colors flex items-center justify-center gap-2">
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
							{{ __('إضافة قسم جديد') }}
						</button>
					</div>
				</div>

				<!-- PANEL 3: Recipe / Packaging / Preview (3/12) -->
				<div class="md:col-span-3 bg-gray-50 p-4 sm:p-6 border-s border-gray-200 overflow-y-auto">
					<div v-if="product.product_type==='standard'&&!hasVariants">
						<div class="text-sm font-bold text-slate-800 mb-5 pb-2 border-b-2 border-gray-200">{{ __('الوصفة / المكونات') }}</div>
						<div class="bg-gray-100 rounded-xl p-5 border border-gray-200 text-center">
							<div v-if="!isEditing" class="text-xs text-gray-400">{{ __('احفظ الصنف أولاً لإدارة الوصفة') }}</div>
							<button v-else @click="openRecipeDialog()" class="w-full py-2.5 rounded-lg border border-blue-300 text-blue-600 text-xs font-medium hover:bg-blue-50">{{ __('إدارة المكونات') }}</button>
						</div>
					</div>
					<div v-if="hasVariants" class="mb-4">
						<div class="text-sm font-bold text-slate-800 mb-3 pb-2 border-b-2 border-gray-200">{{ __('الوصفات') }}</div>
						<div class="bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 text-xs text-blue-700">{{ __('اضغط على أيقونة المكونات بجوار كل variant') }}</div>
					</div>
					<!-- Packaging -->
					<div class="mt-4">
						<div class="text-sm font-bold text-slate-800 mb-3 pb-2 border-b-2 border-gray-200">{{ __('مواد التغليف') }}</div>
						<div v-for="pt in packagingTypes" :key="pt.key" class="rounded-lg border border-gray-200 mb-2 overflow-hidden">
							<button @click="packagingOpen[pt.key]=!packagingOpen[pt.key]" class="w-full flex items-center justify-between px-3 py-2.5 bg-white hover:bg-gray-50 text-xs font-semibold text-gray-700">
								<span class="flex items-center gap-2">{{ pt.icon }} {{ pt.label }} <span v-if="getPackagingList(pt.key).length" class="bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded-full text-[10px]">{{ getPackagingList(pt.key).length }}</span></span>
								<svg :class="['w-4 h-4 transition-transform',packagingOpen[pt.key]?'rotate-180':'']" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
							</button>
							<div v-if="packagingOpen[pt.key]" class="p-3 border-t border-gray-100">
								<div v-for="(pkg,idx) in getPackagingList(pt.key)" :key="idx" class="mb-2 rounded-lg border border-gray-100 bg-gray-50/60 p-2">
									<!-- Item (searchable, full width so the name is readable) -->
									<div class="mb-1.5">
										<SelectInput
											v-model="pkg.item_code"
											:options="packagingOptions"
											:searchable="true"
											:search-placeholder="__('ابحث عن صنف...')"
											:placeholder="__('اختر')"
											:no-results-text="__('لا يوجد نتائج')"
											@change="onPackagingSelect(pkg)"
										/>
									</div>
									<!-- Qty + delete -->
									<div class="flex items-center gap-2">
										<span class="text-[10px] text-gray-400">{{ __('الكمية') }}</span>
										<input v-model.number="pkg.qty" type="number" min="1" class="form-input !py-1 text-xs w-16" dir="ltr"/>
										<button @click="getPackagingList(pt.key).splice(idx,1)" class="ms-auto p-1 text-red-500 hover:bg-red-50 rounded"><svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
									</div>
									<!-- Product Bundle components (nested) -->
									<div v-if="pkg.components && pkg.components.length" class="mt-2 ps-2 border-s-2 border-blue-200 space-y-0.5">
										<div class="text-[10px] text-gray-400 font-semibold">{{ __('المكونات') }}</div>
										<div v-for="(c,ci) in pkg.components" :key="ci" class="flex items-center justify-between text-[11px] text-gray-600">
											<span class="truncate">• {{ c.item_name }}</span>
											<span class="text-gray-400 flex-shrink-0 ms-2">×{{ c.qty }}</span>
										</div>
									</div>
								</div>
								<button @click="addPackaging(pt.key)" class="text-xs text-blue-600 hover:underline">+ {{ __('إضافة') }}</button>
							</div>
						</div>
					</div>
					<!-- Preview -->
					<div v-if="product.item_name||product.custom_item_name_arabic" class="mt-6">
						<div class="text-sm font-bold text-slate-800 mb-3 pb-2 border-b-2 border-gray-200">{{ __('معاينة') }}</div>
						<div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
							<div class="flex items-start gap-3">
								<div class="w-12 h-12 rounded-xl bg-gray-100 flex-shrink-0 flex items-center justify-center overflow-hidden">
									<img v-if="product.image" :src="product.image" class="w-full h-full object-cover"/>
									<svg v-else class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
								</div>
								<div class="flex-1 min-w-0">
									<div class="text-sm font-bold text-gray-800">{{ product.item_name }}</div>
									<div v-if="product.custom_item_name_arabic" class="text-xs text-gray-500">{{ product.custom_item_name_arabic }}</div>
									<div class="text-[10px] text-gray-400 mt-0.5">{{ product.item_group }}</div>
								</div>
							</div>
							<div v-if="hasVariants&&product.variants.length" class="mt-3 pt-3 border-t border-gray-100">
								<div class="text-[10px] font-semibold text-gray-500 uppercase mb-2">{{ __('المتغيرات') }}</div>
								<div class="flex flex-wrap gap-1">
									<span v-for="v in product.variants" :key="v.name" class="px-2 py-0.5 rounded-full bg-gray-100 border border-gray-200 text-[10px] text-gray-700">{{ v.name }}: {{ v.price }} EGP</span>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</main>
		</template>

		<!-- DIALOGS -->
		<!-- Recipe -->
		<div v-if="showRecipeDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
			<div class="w-full max-w-xl bg-white rounded-xl shadow-2xl">
				<div class="flex items-center justify-between border-b px-5 py-3"><h3 class="text-sm font-bold">{{ __('المكونات:') }} {{ currentRecipeItem }}</h3><button @click="showRecipeDialog=false" class="p-1 rounded-lg text-gray-500 hover:bg-gray-100"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button></div>
				<div class="p-5 max-h-[60vh] overflow-y-auto">
					<div v-for="(ing,i) in recipe.ingredients" :key="i" class="mb-2 rounded-lg border border-gray-100 bg-gray-50/60 p-2">
						<!-- Item (searchable, full width) -->
						<div class="mb-1.5">
							<SelectInput
								v-model="ing.item_code"
								:options="rawMaterialOptions"
								:searchable="true"
								:search-placeholder="__('ابحث عن مكون...')"
								:placeholder="__('اختر')"
								:no-results-text="__('لا يوجد نتائج')"
								@change="onIngredientSelect(ing)"
							/>
						</div>
						<!-- Qty + UOM + POS + delete -->
						<div class="flex items-center gap-2">
							<input v-model.number="ing.qty" type="number" min="0.01" step="0.01" class="form-input !py-1 text-xs w-20" dir="ltr"/>
							<select v-model="ing.uom" class="form-input !py-1 text-xs w-24"><option v-for="u in uoms" :key="u.name" :value="u.name">{{ u.name }}</option></select>
							<label class="flex items-center gap-1 text-[10px] whitespace-nowrap"><input v-model="ing.show_in_pos" type="checkbox" class="toggle-cb"/>POS</label>
							<button @click="recipe.ingredients.splice(i,1)" class="ms-auto p-1 text-red-500 hover:bg-red-50 rounded"><svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
						</div>
					</div>
					<button @click="recipe.ingredients.push({item_code:'',item_name:'',qty:1,uom:'Unit',show_in_pos:true})" class="mt-2 text-xs text-blue-600 hover:underline">+ {{ __('إضافة مكون') }}</button>
				</div>
				<div class="flex items-center gap-2 border-t px-5 py-3">
					<button v-if="canDuplicateRecipe" @click="duplicateRecipeToAllVariants" :disabled="savingRecipe" class="px-3 py-2 rounded-lg text-sm font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 disabled:opacity-50" :title="__('نسخ نفس المكونات لكل متغيرات المنتج')">⧉ {{ __('نسخ لكل المتغيرات') }}</button>
					<div class="flex-1"></div>
					<button @click="showRecipeDialog=false" class="px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100">{{ __('إلغاء') }}</button>
					<button @click="saveRecipe" :disabled="savingRecipe" class="px-4 py-2 rounded-lg bg-blue-500 text-white text-sm font-medium hover:bg-blue-600 disabled:opacity-50">{{ __('حفظ المكونات') }}</button>
				</div>
			</div>
		</div>
		<!-- Add Attribute -->
		<div v-if="showAddAttributeDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
			<div class="w-full max-w-sm bg-white rounded-xl shadow-2xl">
				<div class="border-b px-5 py-3"><h3 class="text-sm font-bold">{{ __('إضافة خاصية') }}</h3></div>
				<div class="p-5 space-y-4">
					<div><label class="form-lbl">{{ __('اسم الخاصية') }}</label><select v-model="newAttribute.name" @change="onAttrNameSelect" class="form-input"><option value="">{{ __('اختر...') }}</option><option v-for="n in availableAttributeNames" :key="n" :value="n">{{ n }}</option></select></div>
					<div><label class="form-lbl">{{ __('القيم (مفصولة بفاصلة)') }}</label><input v-model="newAttribute.values" type="text" :placeholder="__('صغير, وسط, كبير')" class="form-input"/></div>
				</div>
				<div class="flex justify-end gap-2 border-t px-5 py-3"><button @click="showAddAttributeDialog=false" class="px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100">{{ __('إلغاء') }}</button><button @click="addAttribute" class="px-4 py-2 rounded-lg bg-blue-500 text-white text-sm font-medium hover:bg-blue-600">{{ __('إضافة') }}</button></div>
			</div>
		</div>
		<!-- Add Addon -->
		<div v-if="showAddAddonDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
			<div class="w-full max-w-sm bg-white rounded-xl shadow-2xl">
				<div class="border-b px-5 py-3"><h3 class="text-sm font-bold">{{ __('إضافة إضافة جديدة') }}</h3></div>
				<div class="p-5 space-y-4">
					<div class="relative"><input v-model="addonSearchQuery" @input="searchAddons" :placeholder="__('ابحث عن صنف...')" class="form-input"/>
						<div v-if="addonSearchResults.length" class="absolute z-10 top-full start-0 mt-1 w-full bg-white rounded-lg shadow-lg border max-h-40 overflow-y-auto"><button v-for="item in addonSearchResults" :key="item.item_code" @click="selectedAddon=item;addonSearchResults=[]" class="w-full text-start px-3 py-2 text-xs hover:bg-blue-50 border-b border-gray-50 last:border-0"><span class="font-medium">{{ item.item_name }}</span></button></div>
					</div>
					<div v-if="selectedAddon" class="bg-blue-50 rounded-lg p-3 text-xs text-blue-800 font-medium">{{ selectedAddon.item_name }}</div>
					<div v-if="selectedAddon"><label class="form-lbl">{{ __('السعر الإضافي') }}</label><input v-model.number="addonPrice" type="number" min="0" class="form-input" dir="ltr"/></div>
				</div>
				<div class="flex justify-end gap-2 border-t px-5 py-3"><button @click="showAddAddonDialog=false;selectedAddon=null;addonSearchQuery=''" class="px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100">{{ __('إلغاء') }}</button><button @click="addAddon" :disabled="!selectedAddon" class="px-4 py-2 rounded-lg bg-blue-500 text-white text-sm font-medium hover:bg-blue-600 disabled:opacity-50">{{ __('إضافة') }}</button></div>
			</div>
		</div>
		<!-- Add Variant to Combo -->
		<div v-if="showAddVariantDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
			<div class="w-full max-w-sm bg-white rounded-xl shadow-2xl">
				<div class="border-b px-5 py-3"><h3 class="text-sm font-bold">{{ __('إضافة variant') }}</h3></div>
				<div class="p-5"><select v-model="selectedVariantToAdd" class="form-input"><option :value="null">{{ __('اختر') }}</option><option v-for="v in availableVariantsForTemplate" :key="v.item_code" :value="v">{{ v.item_name }}</option></select></div>
				<div class="flex justify-end gap-2 border-t px-5 py-3"><button @click="showAddVariantDialog=false" class="px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100">{{ __('إلغاء') }}</button><button @click="confirmAddVariant" :disabled="!selectedVariantToAdd" class="px-4 py-2 rounded-lg bg-blue-500 text-white text-sm font-medium hover:bg-blue-600 disabled:opacity-50">{{ __('إضافة') }}</button></div>
			</div>
		</div>

		<!-- Add New Variant (pick one value per attribute) -->
		<div v-if="showNewVariantDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
			<div class="w-full max-w-sm bg-white rounded-xl shadow-2xl">
				<div class="border-b px-5 py-3"><h3 class="text-sm font-bold">{{ __('إضافة متغير جديد') }}</h3></div>
				<div class="p-5 space-y-3">
					<div v-for="(a, ai) in product.attributes" :key="a.attribute">
						<label class="form-lbl">{{ a.attribute }}</label>
						<input v-model="newVariantSelections[a.attribute]" :list="'attrvals-' + ai" class="form-input" :placeholder="__('اكتب قيمة أو اختر من القائمة')" />
						<datalist :id="'attrvals-' + ai">
							<option v-for="val in a.values" :key="val" :value="val"></option>
						</datalist>
					</div>
				</div>
				<div class="flex justify-end gap-2 border-t px-5 py-3"><button @click="showNewVariantDialog=false" class="px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100">{{ __('إلغاء') }}</button><button @click="confirmNewVariant" class="px-4 py-2 rounded-lg bg-blue-500 text-white text-sm font-medium hover:bg-blue-600">{{ __('إضافة') }}</button></div>
			</div>
		</div>

		<!-- Variant Prices Dialog -->
		<div v-if="showVariantPricesDialog" class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
			<div class="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200 text-right" dir="rtl">
				<div class="bg-slate-800 p-5 flex items-center justify-between text-white">
					<div class="flex items-center gap-3">
						<div class="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center">
							<svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
						</div>
						<div>
							<h3 class="font-bold">{{ __('أسعار المتغير') }}</h3>
							<p class="text-[10px] text-slate-400 uppercase tracking-wider text-left" dir="ltr">{{ currentVariantForPrices?.name }}</p>
						</div>
					</div>
					<button @click="showVariantPricesDialog=false" class="p-2 hover:bg-slate-700 rounded-full transition-colors"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
				</div>
				<div class="p-6 max-h-[60vh] overflow-y-auto">
					<div v-if="currentVariantPrices.length===0" class="text-center py-8 text-gray-400 text-sm italic">{{ __('اضغط + لإضافة سعر جديد') }}</div>
					<div v-for="(p,idx) in currentVariantPrices" :key="idx" class="flex items-center gap-2 mb-3 bg-gray-50 p-3 rounded-xl border border-gray-100">
						<select v-model="p.price_list" class="form-input flex-1 !py-2 text-xs">
							<option v-for="pl in priceLists" :key="pl.name" :value="pl.name">{{ pl.name }}</option>
						</select>
						<div class="flex items-center gap-1 w-28">
							<input v-model.number="p.price" type="number" min="0" class="form-input !py-2 text-xs text-center font-bold text-blue-600" dir="ltr"/>
							<span class="text-[9px] text-gray-400 font-bold">EGP</span>
						</div>
						<button @click="removeVariantPriceRow(idx)" class="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
					</div>
					<button @click="addVariantPriceRow" class="mt-2 w-full py-2 border-2 border-dashed border-gray-200 rounded-xl text-xs font-semibold text-gray-500 hover:border-blue-400 hover:text-blue-500 transition-all flex items-center justify-center gap-2">
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
						{{ __('إضافة سعر لقائمة أخرى') }}
					</button>
				</div>
				<div class="p-4 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
					<button @click="showVariantPricesDialog=false" class="px-5 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-200 rounded-xl transition-colors">{{ __('إلغاء') }}</button>
					<button @click="saveVariantPrices" class="px-6 py-2 bg-slate-800 text-white text-sm font-semibold rounded-xl hover:bg-slate-900 shadow-lg transition-all">{{ __('حفظ الأسعار') }}</button>
				</div>
			</div>
		</div>

		<!-- Extra Prices Dialog (Combo) -->
		<div v-if="showExtraPricesDialog" class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
			<div class="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200 text-right" dir="rtl">
				<div class="bg-slate-800 p-5 flex items-center justify-between text-white">
					<div class="flex items-center gap-3">
						<div class="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center">
							<svg class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
						</div>
						<div>
							<h3 class="font-bold">{{ __('الأسعار الإضافية بالكومبو') }}</h3>
							<p class="text-[10px] text-slate-400 uppercase tracking-wider text-left" dir="ltr">{{ currentOptionForExtraPrices?.item_name }}</p>
						</div>
					</div>
					<button @click="showExtraPricesDialog=false" class="p-2 hover:bg-slate-700 rounded-full transition-colors"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
				</div>
				<div class="p-6 max-h-[60vh] overflow-y-auto">
					<div v-for="(p,idx) in currentExtraPrices" :key="idx" class="flex items-center gap-2 mb-3 bg-amber-50/50 p-3 rounded-xl border border-amber-100">
						<select v-model="p.price_list" class="form-input flex-1 !py-2 text-xs border-amber-200">
							<option v-for="pl in priceLists" :key="pl.name" :value="pl.name">{{ pl.name }}</option>
						</select>
						<div class="flex items-center gap-1 w-28">
							<span class="text-lg font-bold text-amber-600">+</span>
							<input v-model.number="p.price" type="number" min="0" class="form-input !py-2 text-xs text-center font-bold text-amber-700 border-amber-200" dir="ltr"/>
							<span class="text-[9px] text-gray-400 font-bold">EGP</span>
						</div>
						<button @click="removeExtraPriceRow(idx)" class="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
					</div>
					<button @click="addExtraPriceRow" class="mt-2 w-full py-2 border-2 border-dashed border-amber-200 rounded-xl text-xs font-semibold text-amber-600 hover:border-amber-400 hover:bg-amber-50 transition-all flex items-center justify-center gap-2">
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
						{{ __('إضافة سعر لقائمة أخرى') }}
					</button>
				</div>
				<div class="p-4 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
					<button @click="showExtraPricesDialog=false" class="px-5 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-200 rounded-xl transition-colors">{{ __('إلغاء') }}</button>
					<button @click="saveExtraPrices" class="px-6 py-2 bg-slate-800 text-white text-sm font-semibold rounded-xl hover:bg-slate-900 shadow-lg transition-all">{{ __('تحديث الأسعار') }}</button>
				</div>
			</div>
		</div>


		<!-- Global combo item search dropdown (fixed, escapes overflow-hidden parents) -->
		<div v-if="activeOptionSearch && optionSearchResults.length > 0"
			:style="`position:fixed; top:${comboDropdownPos.top}px; left:${comboDropdownPos.left}px; width:${comboDropdownPos.width}px; z-index:9999`"
			class="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden"
			@mousedown.prevent>
			<div class="max-h-64 overflow-y-auto">
				<button v-for="item in optionSearchResults" :key="item.item_code"
					@mousedown.prevent="selectOptionFromDropdown(item)"
					class="w-full text-start px-3 py-2.5 hover:bg-blue-50 border-b border-gray-100 last:border-0 flex items-center gap-2.5 transition-colors">
					<span v-if="item.has_variants" class="text-[9px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full font-bold flex-shrink-0 whitespace-nowrap">Template</span>
					<div class="min-w-0 flex-1">
						<div class="text-sm font-medium text-slate-800 truncate">{{ item.item_name }}</div>
						<div class="text-[11px] text-gray-400 truncate mt-0.5" dir="ltr">{{ item.item_code }}</div>
					</div>
				</button>
			</div>
		</div>

		<!-- Toast -->
		<div v-if="toast.show" :class="['fixed bottom-6 start-1/2 -translate-x-1/2 z-[60] px-5 py-3 rounded-xl shadow-lg text-sm font-medium text-white transition-all',toast.color==='error'?'bg-red-500':toast.color==='warning'?'bg-amber-500':'bg-emerald-500']">{{ toast.message }}</div>
	</div>
</template>

<script setup>
import { call } from "frappe-ui"
import { ref, reactive, computed, onMounted, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import SelectInput from "@/components/common/SelectInput.vue"

// Wrapper: converts frappeCall({ method, args }) → frappe-ui call(method, args)
async function frappeCall({ method, args }) {
	const result = await call(method, args || {})
	return { message: result }
}

const route = useRoute()
const router = useRouter()

// =========================================================================
// State
// =========================================================================
const loading = ref(false)
const saving = ref(false)
const savingInBackground = ref(false)
const isEditing = ref(false)
const hasVariants = ref(false)
const activePriceList = ref("")
const itemId = computed(() => route.params.itemId || null)
const isDeskMode = new URLSearchParams(window.location.search).get("desk") === "1"

// List state
const listItems = ref([])
const listLoading = ref(false)
const listSearch = ref("")
const listFilterGroup = ref("")
const listFilterClassification = ref("")
const listFilterType = ref("")
const listStart = ref(0)
const listPageLength = 20
const listTotal = ref(0)
let listSearchTimer = null

const mode = ref("list") // 'list' | 'editor'

const product = reactive({
	item_code: null, item_name: "", custom_item_name_arabic: "", item_group: "",
	standard_rate: 0, image: "", product_type: "standard",
	custom_is_pos_item: true, custom_fast_sell: false,
	attributes: [], variants: [], sections: [], addons: [], addons_label: "",
	packaging_delivery: [], packaging_dinein: [], packaging_takeaway: [],
	custom_item_classification: "",
})

const packagingOpen = reactive({ delivery: false, dinein: false, takeaway: false })
const packagingItems = ref([])
const packagingOptions = computed(() => packagingItems.value.map((pi) => ({
	value: pi.item_code,
	label: (pi.item_name || pi.item_code) + (pi.enabled_item_bundle ? " 📦" : ""),
	subtitle: pi.item_code,
})))
const packagingTypes = [
	{ key: "delivery", label: "Delivery", icon: "\uD83D\uDE9A" },
	{ key: "dinein", label: "Dine-in", icon: "\uD83C\uDF7D\uFE0F" },
	{ key: "takeaway", label: "Takeaway", icon: "\uD83D\uDECD\uFE0F" },
]

const priceLists = ref([])
const itemPrices = ref([])
const categories = ref([])
const classifications = ref([])
const availableItems = ref([])
const availableAttributes = ref([])

const showAddAddonDialog = ref(false)
const addonSearchQuery = ref("")
const addonSearchResults = ref([])
const selectedAddon = ref(null)
const addonPrice = ref(0)

const showAddAttributeDialog = ref(false)
const newAttribute = reactive({ name: "", values: "" })

const showVariantPricesDialog = ref(false)
const currentVariantForPrices = ref(null)
const currentVariantPrices = ref([])

const showExtraPricesDialog = ref(false)
const currentOptionForExtraPrices = ref(null)
const currentExtraPrices = ref([])

const showRecipeDialog = ref(false)
const savingRecipe = ref(false)
const currentRecipeItem = ref(null)
const recipe = reactive({ bundle_name: null, ingredients: [] })
const rawMaterials = ref([])
const rawMaterialOptions = computed(() => rawMaterials.value.map((rm) => ({
	value: rm.item_code,
	label: rm.item_name || rm.item_code,
	subtitle: rm.item_code,
})))
const uoms = ref([])

const showNewVariantDialog = ref(false)
const newVariantSelections = reactive({})
const showAddVariantDialog = ref(false)
const currentTemplateOption = ref(null)
const selectedVariantToAdd = ref(null)
const availableVariantsForTemplate = ref([])

const activeOptionSearch = ref(null)
const optionSearchResults = ref([])
const comboDropdownPos = reactive({ top: 0, left: 0, width: 300 })
const activeOptionContext = ref(null) // { opt, sec }

const sectionTypes = [
	{ value: "Component", label: "\u0645\u0643\u0648\u0646" },
	{ value: "Attribute", label: "\u062E\u0627\u0635\u064A\u0629" },
	{ value: "Package", label: "\u0628\u0627\u0642\u0629" },
	{ value: "Add-On", label: "\u0625\u0636\u0627\u0641\u0629" },
]

const toast = reactive({ show: false, message: "", color: "success" })

// =========================================================================
// Computed
// =========================================================================
const productTypeLabel = computed(() => {
	if (product.product_type === "combo") return __("\u0648\u062C\u0628\u0629 \u0643\u0648\u0645\u0628\u0648")
	if (hasVariants.value) return __("\u0648\u062C\u0628\u0629 \u0639\u0627\u062F\u064A\u0629 \u0645\u0639 Variants")
	return __("\u0648\u062C\u0628\u0629 \u0639\u0627\u062F\u064A\u0629")
})

const canSave = computed(() => !!((product.item_name || product.custom_item_name_arabic) && product.item_group))

const availableAttributeNames = computed(() => availableAttributes.value.map((a) => a.name))

const collapsedGroups = reactive({})

function toggleGroup(key) {
	collapsedGroups[key] = !collapsedGroups[key]
}

const flatVariantTree = computed(() => {
	if (!product.variants.length) return []
	const attrs = product.attributes
	if (!attrs.length) return product.variants.map(v => ({ type: 'leaf', variant: v, level: 0, label: v.name }))

	const rows = []

	function buildRows(variants, attrIdx, pathKey) {
		if (!variants.length) return
		const attr = attrs[attrIdx]
		if (!attr) {
			variants.forEach(v => rows.push({ type: 'leaf', variant: v, level: attrIdx, label: v.name }))
			return
		}
		const isLastAttr = attrIdx === attrs.length - 1
		const groups = {}
		const order = []
		variants.forEach(v => {
			const val = (v.attributes && v.attributes[attr.attribute]) || v.name || '?'
			if (!groups[val]) { groups[val] = []; order.push(val) }
			groups[val].push(v)
		})
		const sortedVals = attr.values
			? [...attr.values.filter(val => groups[val]), ...order.filter(val => !(attr.values || []).includes(val))]
			: order
		sortedVals.forEach(val => {
			const groupKey = `${pathKey}/${val}`
			if (isLastAttr) {
				groups[val].forEach(v => rows.push({ type: 'leaf', variant: v, level: attrIdx, label: val, attrName: attr.attribute }))
			} else {
				const collapsed = !!collapsedGroups[groupKey]
				rows.push({ type: 'group', label: val, attr: attr.attribute, level: attrIdx, count: groups[val].length, key: groupKey, collapsed })
				if (!collapsed) buildRows(groups[val], attrIdx + 1, groupKey)
			}
		})
	}

	buildRows(product.variants, 0, '')
	return rows
})

const expectedVariantsCount = computed(() => {
	if (product.attributes.length === 0) return 0
	return product.attributes.reduce((total, attr) => total * (attr.values.length || 1), 1)
})

// =========================================================================
// Helpers
// =========================================================================
function goBack() {
	if (isDeskMode) { window.location.href = "/app"; return }
	router.push({ name: "POSSale" })
}

function goBackToList() {
	if (route.params.itemId) {
		router.push({ name: "NewProductEditor" })
		return
	}
	resetEditor()
	mode.value = "list"
	loadListItems()
}

async function startCreate() {
	resetEditor()
	mode.value = "editor"
	await loadAvailableItems()
}

async function editItemFromList(item) {
	resetEditor()
	mode.value = "editor"
	await loadAvailableItems()
	loadProduct(item.name || item.item_code)
}

function duplicateItem(item) {
	resetEditor()
	product.item_name = (item.item_name || '') + ' (Copy)'
	product.custom_item_name_arabic = item.custom_item_name_arabic || ''
	product.item_group = item.item_group || ''
	product.standard_rate = item.standard_rate || 0
	product.image = item.image || ''
	mode.value = "editor"
}

function resetEditor() {
	isEditing.value = false; hasVariants.value = false; saving.value = false
	product.item_code = null; product.item_name = ""; product.custom_item_name_arabic = ""
	product.item_group = ""; product.standard_rate = 0; product.image = ""
	product.product_type = "standard"; product.custom_is_pos_item = true; product.custom_fast_sell = false
	product.attributes = []; product.variants = []; product.sections = []
	product.addons = []; product.addons_label = ""
	product.packaging_delivery = []; product.packaging_dinein = []; product.packaging_takeaway = []
	itemPrices.value = []
}

// =========================================================================
// List
// =========================================================================
function onListSearch() {
	if (listSearchTimer) clearTimeout(listSearchTimer)
	listSearchTimer = window.setTimeout(() => { listStart.value = 0; loadListItems() }, 300)
}

function refreshList() { listStart.value = 0; loadListItems() }

function formatCurrency(value) { return parseFloat(value || 0).toFixed(2) }

async function loadListItems() {
	listLoading.value = true
	try {
		const res = await frappeCall({
			method: "ecs_posnext.api.item_manager.get_item_manager_items",
			args: {
				search_term: listSearch.value || "",
				start: listStart.value,
				page_length: listPageLength,
				item_group: listFilterGroup.value || "",
				item_classification: listFilterClassification.value || "",
				item_type: listFilterType.value || "",
			},
		})
		const data = res.message || {}
		listItems.value = data.items || []
		listTotal.value = data.total || 0
	} catch (e) { console.error(e) }
	listLoading.value = false
}

function addPriceRow() {
	const defaultPL = priceLists.value.length > 0 ? priceLists.value[0].name : ""
	itemPrices.value.push({ price_list: defaultPL, price: 0 })
}

function showMessage(msg, color = "success") {
	toast.show = true; toast.message = msg; toast.color = color
	window.setTimeout(() => { toast.show = false }, 3000)
}

function getPackagingList(key) {
	if (key === "delivery") return product.packaging_delivery
	if (key === "dinein") return product.packaging_dinein
	return product.packaging_takeaway
}

function addPackaging(key) { getPackagingList(key).push({ item_code: "", qty: 1, uom: "Unit" }) }

// =========================================================================
// Attributes
// =========================================================================
function onAttrNameSelect() {
	const attr = availableAttributes.value.find((a) => a.name === newAttribute.name)
	if (attr && attr.values) {
		newAttribute.values = attr.values.map((v) => v.attribute_value || v.value || v).join(", ")
	}
}

function addAttribute() {
	if (!newAttribute.name || !newAttribute.values) { showMessage(__("\u0623\u062F\u062E\u0644 \u0627\u0633\u0645 \u0627\u0644\u062E\u0627\u0635\u064A\u0629 \u0648\u0627\u0644\u0642\u064A\u0645"), "warning"); return }
	const values = newAttribute.values.split(",").map((v) => v.trim()).filter((v) => v)
	// If the attribute already exists, merge new values into it (lets the user
	// add a new value to an existing attribute, then re-generate to add combos).
	const existing = product.attributes.find((a) => a.attribute === newAttribute.name)
	if (existing) {
		for (const val of values) if (!existing.values.includes(val)) existing.values.push(val)
	} else {
		product.attributes.push({ attribute: newAttribute.name, values })
	}
	newAttribute.name = ""; newAttribute.values = ""
	showAddAttributeDialog.value = false
}

function removeAttribute(attr) {
	const i = product.attributes.indexOf(attr)
	if (i > -1) {
		product.attributes.splice(i, 1)
		// In create mode clear the generated list; when editing keep existing
		// variants intact so we never wipe saved data from the UI.
		if (!isEditing.value) product.variants = []
	}
}

// =========================================================================
// Addons
// =========================================================================
let addonSearchTimer = null
function searchAddons() {
	if (addonSearchTimer) clearTimeout(addonSearchTimer)
	addonSearchTimer = window.setTimeout(async () => {
		if (!addonSearchQuery.value || addonSearchQuery.value.length < 2) { addonSearchResults.value = []; return }
		try {
			const res = await frappeCall({ method: "frappe.client.get_list", args: { doctype: "Item", fields: ["item_code", "item_name", "standard_rate"], filters: { item_name: ["like", `%${addonSearchQuery.value}%`], disabled: 0 }, limit_page_length: 20 } })
			addonSearchResults.value = res.message || []
		} catch (e) { console.error(e) }
	}, 300)
}

function addAddon() {
	if (!selectedAddon.value) return
	if (product.addons.find((a) => a.item_code === selectedAddon.value.item_code)) { showMessage(__("\u0645\u0636\u0627\u0641 \u0645\u0633\u0628\u0642\u0627\u064B"), "warning"); return }
	product.addons.push({ item_code: selectedAddon.value.item_code, item_name: selectedAddon.value.item_name, price: addonPrice.value || 0 })
	selectedAddon.value = null; addonPrice.value = 0; addonSearchQuery.value = ""
	showAddAddonDialog.value = false
}

// =========================================================================
// Variants
// =========================================================================
function _variantBaseCode() {
	if (product.item_code) return product.item_code
	return (product.item_name || "ITEM").toUpperCase().replace(/[^A-Z0-9]/g, "").substring(0, 6) || "ITEM"
}

// Stable signature for a variant's attribute combination. Handles both shapes:
// existing variants store attributes as an object {attr: value}; freshly
// generated ones as an array [{attribute, value}].
function _variantAttrSig(variant) {
	const attrs = variant.attributes
	let pairs = []
	if (Array.isArray(attrs)) pairs = attrs.map((a) => [a.attribute, a.value])
	else if (attrs && typeof attrs === "object") pairs = Object.entries(attrs)
	return pairs.map(([k, v]) => `${k}=${v}`).sort().join("|")
}

function generateAllVariants() {
	if (product.attributes.length === 0) return
	const arrays = product.attributes.map((a) => a.values)
	let combos = [[]]
	for (const arr of arrays) { const n = []; combos.forEach((c) => { arr.forEach((v) => { n.push([...c, v]) }) }); combos = n }
	const baseCode = _variantBaseCode()
	const basePrice = (itemPrices.value.length > 0 && itemPrices.value[0].price) ? itemPrices.value[0].price : (product.standard_rate || 0)
	// Preserve already-saved variants (keyed by attribute combination) so that
	// re-generating while EDITING only ADDS the missing combos and never wipes
	// existing variants (with their prices / disabled state).
	const existingBySig = {}
	for (const v of product.variants) {
		if (v.isExisting) existingBySig[_variantAttrSig(v)] = v
	}
	// Track codes — Arabic/short values can truncate to the same suffix, so
	// disambiguate collisions to keep every code unique.
	const usedCodes = new Set(product.variants.map((v) => v.item_code).filter(Boolean))
	product.variants = combos.map((combo) => {
		const sig = product.attributes.map((a, i) => `${a.attribute}=${combo[i]}`).sort().join("|")
		if (existingBySig[sig]) return existingBySig[sig] // keep the existing variant as-is
		const suffix = combo.join(" - ")
		const codeSuffix = combo.map((v) => v.replace(/\s+/g, "").substring(0, 4).toUpperCase()).join("-")
		let code = `${baseCode}-${codeSuffix}`
		if (usedCodes.has(code)) {
			let i = 2
			while (usedCodes.has(`${code}-${i}`)) i++
			code = `${code}-${i}`
		}
		usedCodes.add(code)
		return {
			name: suffix,
			attributes: product.attributes.map((a, i) => ({ attribute: a.attribute, value: combo[i] })),
			price: basePrice,
			item_code: code,
			isExisting: false,
			show_bundle: false,
		}
	})
}

function addVariantManually() {
	// Template with attributes → open a dialog to pick one value per attribute
	// so the new variant has a valid attribute combination (otherwise it renders
	// as an empty/broken row and fails variant validation on save).
	if (product.attributes.length > 0) {
		Object.keys(newVariantSelections).forEach((k) => delete newVariantSelections[k])
		for (const a of product.attributes) newVariantSelections[a.attribute] = a.values[0] || ""
		showNewVariantDialog.value = true
		return
	}
	// No attributes → simple "Type"-based blank row.
	const base = _variantBaseCode()
	const num = String(product.variants.length + 1).padStart(2, "0")
	product.variants.push({ name: "", price: 0, item_code: `${base}-V${num}`, isExisting: false, show_bundle: false, attributes: [] })
}

function confirmNewVariant() {
	const combo = product.attributes.map((a) => ({ attribute: a.attribute, value: (newVariantSelections[a.attribute] || "").trim() }))
	if (combo.some((c) => !c.value)) { showMessage(__("اكتب قيمة لكل خاصية"), "warning"); return }
	const sig = combo.map((c) => `${c.attribute}=${c.value}`).sort().join("|")
	if (product.variants.some((v) => _variantAttrSig(v) === sig)) {
		showMessage(__("هذا المتغير موجود بالفعل"), "warning"); return
	}
	// Register any newly-typed value on its attribute so it gets added to the
	// Item Attribute's allowed values on save (otherwise variant validation fails).
	for (const c of combo) {
		const attr = product.attributes.find((a) => a.attribute === c.attribute)
		if (attr && !attr.values.includes(c.value)) attr.values.push(c.value)
	}
	const baseCode = _variantBaseCode()
	const usedCodes = new Set(product.variants.map((v) => v.item_code).filter(Boolean))
	const codeSuffix = combo.map((c) => String(c.value).replace(/\s+/g, "").substring(0, 4).toUpperCase()).join("-")
	let code = `${baseCode}-${codeSuffix}`
	if (usedCodes.has(code)) { let i = 2; while (usedCodes.has(`${code}-${i}`)) i++; code = `${code}-${i}` }
	const basePrice = (itemPrices.value.length > 0 && itemPrices.value[0].price) ? itemPrices.value[0].price : (product.standard_rate || 0)
	product.variants.push({
		name: combo.map((c) => c.value).join(" - "),
		attributes: combo,
		price: basePrice,
		item_code: code,
		isExisting: false,
		show_bundle: false,
	})
	showNewVariantDialog.value = false
}

function removeVariantByName(name) {
	const i = product.variants.findIndex((v) => v.name === name)
	if (i > -1) product.variants.splice(i, 1)
}

// =========================================================================
// Combo Option Search
// =========================================================================
let optionSearchTimer = null

function _updateDropdownPos(inputEl) {
	const rect = inputEl.getBoundingClientRect()
	comboDropdownPos.top = rect.bottom + 4
	comboDropdownPos.left = rect.left
	comboDropdownPos.width = Math.max(rect.width, 300)
}

async function startOptionSearch(event, opt, si, oi) {
	_updateDropdownPos(event.target)
	activeOptionContext.value = { opt, si, oi }
	activeOptionSearch.value = `${si}-${oi}`
	optionSearchResults.value = []
	const res = await frappeCall({ method: "frappe.client.get_list", args: {
		doctype: "Item", fields: ["item_code", "item_name", "has_variants", "variant_of"],
		filters: { disabled: 0, variant_of: ["is", "not set"] },
		order_by: "modified desc", limit_page_length: 20,
	}})
	if (activeOptionSearch.value === `${si}-${oi}`) optionSearchResults.value = res.message || []
}

function onOptionSearchInput(event, opt, si, oi) {
	const q = event.target.value
	opt.item_name = q
	_updateDropdownPos(event.target)
	activeOptionContext.value = { opt, si, oi }
	activeOptionSearch.value = `${si}-${oi}`
	if (optionSearchTimer) clearTimeout(optionSearchTimer)
	optionSearchTimer = window.setTimeout(async () => {
		if (!q || q.length < 1) { optionSearchResults.value = []; return }
		const res = await frappeCall({ method: "frappe.client.get_list", args: {
			doctype: "Item", fields: ["item_code", "item_name", "has_variants", "variant_of"],
			filters: { disabled: 0 },
			or_filters: [["item_code", "like", `%${q}%`], ["item_name", "like", `%${q}%`]],
			order_by: "modified desc", limit_page_length: 20,
		}})
		if (activeOptionSearch.value === `${si}-${oi}`) optionSearchResults.value = res.message || []
	}, 250)
}

function selectOptionFromDropdown(item) {
	if (!activeOptionContext.value) return
	const { opt, si, oi } = activeOptionContext.value
	const sec = product.sections[si]
	if (sec) selectOption(opt, item, sec)
	activeOptionSearch.value = null
	optionSearchResults.value = []
}

async function selectOption(opt, item, section) {
	opt.item_code = item.item_code; opt.item_name = item.item_name
	activeOptionSearch.value = null; optionSearchResults.value = []
	if (item.has_variants && !item.variant_of) {
		opt.has_variants = true; opt.expanded = true
		const res = await frappeCall({ method: "frappe.client.get_list", args: { doctype: "Item", fields: ["item_code", "item_name", "standard_rate"], filters: { variant_of: item.item_code, disabled: 0 }, limit_page_length: 0 } })
		opt.variants = (res.message || []).map((v) => ({ item_code: v.item_code, item_name: v.item_name, extra_price: 0, default_selected: false, qty: 1 }))
	} else { opt.has_variants = false; opt.variants = null }
}

function applyGlobalPrice(opt) {
	if (opt.variants && opt.global_price !== undefined) {
		opt.variants.forEach((v) => {
			v.extra_price = opt.global_price
		})
	}
}

// Returns deduplicated attribute names from a variant group's variants
function getVariantAttributes(opt) {
	const attrs = new Set()
	;(opt.variants || []).forEach(vr => {
		;(vr.attributes || []).forEach(a => attrs.add(a.attribute))
	})
	return Array.from(attrs)
}

function toggleLockedAttribute(opt, attr) {
	if (!opt.locked_attributes) opt.locked_attributes = []
	const idx = opt.locked_attributes.indexOf(attr)
	if (idx >= 0) opt.locked_attributes.splice(idx, 1)
	else opt.locked_attributes.push(attr)
}

async function openAddVariantDialog(opt) {
	currentTemplateOption.value = opt; selectedVariantToAdd.value = null
	const res = await frappeCall({ method: "frappe.client.get_list", args: { doctype: "Item", filters: { variant_of: opt.item_code }, fields: ["item_code", "item_name"], limit_page_length: 0 } })
	const existing = (opt.variants || []).map((v) => v.item_code)
	availableVariantsForTemplate.value = (res.message || []).filter((v) => !existing.includes(v.item_code))
	showAddVariantDialog.value = true
}

function confirmAddVariant() {
	if (!selectedVariantToAdd.value || !currentTemplateOption.value) return
	if (!currentTemplateOption.value.variants) currentTemplateOption.value.variants = []
	currentTemplateOption.value.variants.push({ item_code: selectedVariantToAdd.value.item_code, item_name: selectedVariantToAdd.value.item_name, extra_price: 0, extra_price_json: {}, default_selected: false, qty: 1 })
	showAddVariantDialog.value = false
}

// =========================================================================
// Recipe
// =========================================================================
async function openRecipeDialog(variant = null) {
	currentRecipeItem.value = variant ? variant.item_code : product.item_code
	recipe.bundle_name = null; recipe.ingredients = []
	await Promise.all([loadRawMaterials(), loadUOMs()])
	await loadExistingBundle()
	showRecipeDialog.value = true
}

async function loadRawMaterials() {
	const res = await frappeCall({ method: "frappe.client.get_list", args: { doctype: "Item", fields: ["item_code", "item_name", "stock_uom"], filters: { is_stock_item: 1, disabled: 0 }, limit_page_length: 0 } })
	rawMaterials.value = res.message || []
}

async function loadUOMs() {
	const res = await frappeCall({ method: "frappe.client.get_list", args: { doctype: "UOM", fields: ["name"], limit_page_length: 0 } })
	uoms.value = res.message || []
}

async function loadExistingBundle() {
	const res = await frappeCall({ method: "frappe.client.get_list", args: { doctype: "Product Bundle", filters: { new_item_code: currentRecipeItem.value }, fields: ["name"], limit_page_length: 1 } })
	if (res.message && res.message.length > 0) {
		recipe.bundle_name = res.message[0].name
		const b = await frappeCall({ method: "frappe.client.get", args: { doctype: "Product Bundle", name: recipe.bundle_name } })
		if (b.message && b.message.items) {
			recipe.ingredients = b.message.items.map((r) => ({ item_code: r.item_code, item_name: r.description || r.item_code, qty: r.qty, uom: r.uom || "Unit", show_in_pos: r.show_in_pos !== 0 }))
		}
	}
}

function onIngredientSelect(ing) {
	const item = rawMaterials.value.find((i) => i.item_code === ing.item_code)
	if (item) { ing.item_name = item.item_name; ing.uom = item.stock_uom || "Unit" }
}

async function saveRecipe() {
	if (recipe.ingredients.length === 0) { showMessage(__("\u0623\u0636\u0641 \u0645\u0643\u0648\u0646 \u0648\u0627\u062D\u062F"), "error"); return }
	savingRecipe.value = true
	try {
		const validItems = recipe.ingredients.filter((ing) => ing.item_code)
		if (validItems.length === 0) { showMessage(__("أضف مكوّن صحيح واحد على الأقل"), "error"); savingRecipe.value = false; return }
		if (recipe.bundle_name) await frappeCall({ method: "frappe.client.delete", args: { doctype: "Product Bundle", name: recipe.bundle_name } })
		const doc = { doctype: "Product Bundle", new_item_code: currentRecipeItem.value, items: validItems.map((ing) => ({ item_code: ing.item_code, qty: ing.qty, uom: ing.uom, description: ing.item_name, show_in_pos: ing.show_in_pos ? 1 : 0 })) }
		const res = await frappeCall({ method: "frappe.client.insert", args: { doc } })
		recipe.bundle_name = res.message.name
		showMessage(__("\u062A\u0645 \u062D\u0641\u0638 \u0627\u0644\u0645\u0643\u0648\u0646\u0627\u062A"))
		showRecipeDialog.value = false
	} catch (e) { showMessage(e.message || __("\u062E\u0637\u0623"), "error") }
	savingRecipe.value = false
}

// Show "duplicate to all variants" only when editing a variant's recipe and
// the template has more than one variant.
const canDuplicateRecipe = computed(() =>
	product.variants.filter((v) => v.item_code).length > 1 &&
	product.variants.some((v) => v.item_code === currentRecipeItem.value)
)

// Copy the current recipe components to EVERY variant of the template.
async function duplicateRecipeToAllVariants() {
	if (recipe.ingredients.length === 0) { showMessage(__("\u0623\u0636\u0641 \u0645\u0643\u0648\u0646 \u0648\u0627\u062D\u062F \u0639\u0644\u0649 \u0627\u0644\u0623\u0642\u0644"), "error"); return }
	const targets = product.variants.filter((v) => v.item_code)
	if (targets.length === 0) return
	const items = recipe.ingredients
		.filter((ing) => ing.item_code)
		.map((ing) => ({
			item_code: ing.item_code, qty: ing.qty, uom: ing.uom,
			description: ing.item_name, show_in_pos: ing.show_in_pos ? 1 : 0,
		}))
	if (items.length === 0) { showMessage(__("أضف مكوّن صحيح واحد على الأقل"), "error"); return }
	savingRecipe.value = true
	try {
		for (const v of targets) {
			const ex = await frappeCall({ method: "frappe.client.get_list", args: { doctype: "Product Bundle", filters: { new_item_code: v.item_code }, fields: ["name"], limit_page_length: 1 } })
			if (ex.message && ex.message.length) {
				await frappeCall({ method: "frappe.client.delete", args: { doctype: "Product Bundle", name: ex.message[0].name } })
			}
			await frappeCall({ method: "frappe.client.insert", args: { doc: { doctype: "Product Bundle", new_item_code: v.item_code, items } } })
		}
		showMessage(__("\u062A\u0645 \u0646\u0633\u062E \u0627\u0644\u0645\u0643\u0648\u0646\u0627\u062A \u0625\u0644\u0649 {0} \u0645\u062A\u063A\u064A\u0631", [targets.length]))
		showRecipeDialog.value = false
	} catch (e) {
		console.error(e)
		showMessage(e.message || __("\u0641\u0634\u0644 \u0646\u0633\u062E \u0627\u0644\u0645\u0643\u0648\u0646\u0627\u062A"), "error")
	} finally {
		savingRecipe.value = false
	}
}

// Watch for route changes to handle direct item editing via URL
watch(
	() => route.params.itemId,
	(newId) => {
		if (newId) {
			loadData()
		} else if (mode.value !== "list") {
			goBackToList()
		}
	},
)

// =========================================================================
// Data Loading
// =========================================================================
async function loadData() {
	loading.value = true
	try {
		await Promise.all([loadCategories(), loadClassifications(), loadAvailableAttributes(), loadPackagingItems()])
		const id = itemId.value
		if (id && id !== "new") {
			mode.value = "editor"
			await loadProduct(id)
		} else if (id === "new") {
			mode.value = "editor"
		} else {
			mode.value = "list"
			await loadListItems()
		}
	} catch (e) { console.error(e); showMessage(__("\u062E\u0637\u0623 \u0641\u064A \u062A\u062D\u0645\u064A\u0644 \u0627\u0644\u0628\u064A\u0627\u0646\u0627\u062A"), "error") }
	loading.value = false
}

async function loadCategories() {
	const res = await frappeCall({ method: "frappe.client.get_list", args: { doctype: "Item Group", fields: ["name"], limit_page_length: 0 } })
	categories.value = res.message || []
}

async function loadClassifications() {
	try {
		const res = await frappeCall({ method: "frappe.client.get_list", args: { doctype: "Item Classification", fields: ["name"], limit_page_length: 0 } })
		classifications.value = res.message || []
	} catch (e) { classifications.value = [] }
}

async function loadAvailableItems() {
	const res = await frappeCall({ method: "frappe.client.get_list", args: { doctype: "Item", fields: ["item_code", "item_name", "standard_rate", "has_variants", "variant_of"], filters: { disabled: 0 }, limit_page_length: 0 } })
	availableItems.value = res.message || []
}

async function loadAvailableAttributes() {
	const res = await frappeCall({ method: "ecs_posnext.api.item_manager.get_item_attributes", args: {} })
	availableAttributes.value = res.message || []
}

async function loadPackagingItems() {
	// Show ALL items (not only stock items). Exclude disabled items and
	// templates (a template itself can't be used as a packaging material).
	const res = await frappeCall({ method: "frappe.client.get_list", args: {
		doctype: "Item",
		fields: ["item_code", "item_name", "enabled_item_bundle"],
		filters: { disabled: 0, has_variants: 0 },
		limit_page_length: 0,
	} })
	packagingItems.value = res.message || []
}

async function onPackagingSelect(pkg) {
	pkg.components = []
	if (!pkg.item_code) return
	const pi = packagingItems.value.find((i) => i.item_code === pkg.item_code)
	if (!pi || !pi.enabled_item_bundle) return
	try {
		const res = await frappeCall({ method: "ecs_posnext.api.item_manager.get_product_bundle", args: { item_code: pkg.item_code } })
		if (res.message && res.message.exists) pkg.components = res.message.items || []
	} catch (e) { console.error("Failed to load bundle components", e) }
}

async function loadProduct(id) {
	isEditing.value = true
	const res = await frappeCall({ method: "frappe.client.get", args: { doctype: "Item", name: id } })
	if (!res.message) return
	const item = res.message
	product.item_code = item.item_code; product.item_name = item.item_name
	product.custom_item_name_arabic = item.custom_item_name_arabic || ""
	product.item_group = item.item_group; product.standard_rate = item.standard_rate || 0
	product.image = item.image || ""; product.custom_is_pos_item = item.custom_is_pos_item
	product.custom_fast_sell = item.custom_fast_sell
	product.product_type = item.enabled_item_bundle ? "combo" : "standard"
	hasVariants.value = item.has_variants === 1

	product.packaging_delivery = (item.packaging_delivery || []).map((p) => ({ item_code: p.item_code, qty: p.qty || 1 }))
	product.packaging_dinein = (item.packaging_dinein || []).map((p) => ({ item_code: p.item_code, qty: p.qty || 1 }))
	product.packaging_takeaway = (item.packaging_takeaway || []).map((p) => ({ item_code: p.item_code, qty: p.qty || 1 }))
	// Resolve bundle components for any packaging "kit" so they show nested.
	for (const list of [product.packaging_delivery, product.packaging_dinein, product.packaging_takeaway]) {
		for (const pkg of list) await onPackagingSelect(pkg)
	}
	product.addons = (item.custom_addons || []).map((a) => ({ item_code: a.item_code, item_name: a.item_name, price: a.price || 0 }))
	product.addons_label = item.custom_addons_label || ""

	if (item.enabled_item_bundle && item.combo_components) await loadComboSections(item.combo_components)
	if (item.has_variants) {
		// Optimized: loadVariants now handles both variants and their attributes
		await loadVariants()
		// Load item prices from first variant (templates can't have Item Prices)
		if (product.variants.length > 0 && product.variants[0].item_code) {
			await loadItemPrices(product.variants[0].item_code)
		}
	} else {
		await loadItemPrices(item.item_code)
	}
}

async function loadItemPrices(code) {
	const res = await frappeCall({ method: "frappe.client.get_list", args: { doctype: "Item Price", fields: ["name", "price_list", "price_list_rate"], filters: { item_code: code, selling: 1 }, limit_page_length: 0 } })
	itemPrices.value = (res.message || []).map((p) => ({ name: p.name, price_list: p.price_list, price: p.price_list_rate }))
}

async function loadComboSections(components) {
	const codes = components.map((c) => c.item_code)
	const r = await frappeCall({ method: "frappe.client.get_list", args: { doctype: "Item", fields: ["item_code", "item_name", "variant_of"], filters: { item_code: ["in", codes] }, limit_page_length: 0 } })
	const map = {}; (r.message || []).forEach((i) => { map[i.item_code] = i })
	const sectionsMap = {}; const templateGroups = {}
	components.forEach((c) => {
		const sn = c.section_name || "Default"
		if (!sectionsMap[sn]) sectionsMap[sn] = { name: sn, section_type: c.section_type || "Component", is_required: c.is_required === 1, min_qty: c.min_qty || 0, max_qty: c.max_qty || 1, options: [] }
		const info = map[c.item_code] || {}; const tpl = info.variant_of
		
		let extraPricesArray = []
		try {
			if (c.extra_prices && typeof c.extra_prices === 'string' && c.extra_prices.startsWith('[')) {
				extraPricesArray = JSON.parse(c.extra_prices)
			}
		} catch(e) { console.error("Error parsing extra_prices", e) }

		const optData = {
			item_code: c.item_code,
			item_name: info.item_name || c.item_code,
			extra_price: c.extra_price || 0,
			extra_prices: extraPricesArray,
			default_selected: c.default_selected === 1,
			qty: c.qty || 1,
			locked_attributes: c.locked_attributes || "[]",
			lock_group: c.lock_group || "",
		}

		if (tpl && c.is_standalone !== 1) {
			const key = `${sn}__${tpl}`
			if (!templateGroups[key]) templateGroups[key] = { sn, tpl, variants: [] }
			templateGroups[key].variants.push({ ...optData })
		} else { 
			sectionsMap[sn].options.push({ ...optData, has_variants: false }) 
		}
	})
	const tplCodes = [...new Set(Object.values(templateGroups).map(g => g.tpl))]
	const tplMap = {}
	if (tplCodes.length) {
		const tplRes = await frappeCall({ method: "frappe.client.get_list", args: {
			doctype: "Item", fields: ["item_code", "item_name"],
			filters: { item_code: ["in", tplCodes] }, limit_page_length: 0,
		}})
		;(tplRes.message || []).forEach(t => { tplMap[t.item_code] = t.item_name })
	}

	// Fetch variant attributes for all variant items so the locked-attributes UI can show them
	const variantCodes = Object.values(templateGroups).flatMap(g => g.variants.map(v => v.item_code))
	const attrMap = {}
	if (variantCodes.length) {
		const attrRes = await frappeCall({ method: "ecs_posnext.api.items.get_variant_attributes", args: { item_codes: variantCodes } })
		;(attrRes.message || []).forEach(a => {
			if (!attrMap[a.parent]) attrMap[a.parent] = []
			attrMap[a.parent].push({ attribute: a.attribute, value: a.value })
		})
	}
	// Attach attributes to each variant
	Object.values(templateGroups).forEach(g => {
		g.variants.forEach(vr => { vr.attributes = attrMap[vr.item_code] || [] })
	})

	for (const key in templateGroups) {
		const g = templateGroups[key]
		const la = (() => { try { return JSON.parse(g.variants[0]?.locked_attributes || "[]") } catch { return [] } })()
		sectionsMap[g.sn].options.push({ item_code: g.tpl, item_name: tplMap[g.tpl] || g.tpl, has_variants: true, expanded: true, variants: g.variants, qty: g.variants[0]?.qty || 1, locked_attributes: la })
	}
	product.sections = Object.values(sectionsMap)
}

async function loadAttributesFromVariants() {
	const res = await frappeCall({ method: "frappe.client.get_list", args: { doctype: "Item", fields: ["item_code"], filters: { variant_of: product.item_code }, limit_page_length: 0 } })
	const variants = res.message || []; if (!variants.length) return
	const attrMap = {}
	for (const v of variants) {
		const d = await frappeCall({ method: "frappe.client.get", args: { doctype: "Item", name: v.item_code } })
		if (d.message && d.message.attributes) {
			d.message.attributes.forEach((a) => {
				if (!attrMap[a.attribute]) attrMap[a.attribute] = { attribute: a.attribute, values: [] }
				if (a.attribute_value && !attrMap[a.attribute].values.includes(a.attribute_value)) attrMap[a.attribute].values.push(a.attribute_value)
			})
		}
	}
	product.attributes = Object.values(attrMap)
}

async function loadVariants() {
	const res = await frappeCall({
		method: "ecs_posnext.api.item_manager.get_editor_variants",
		args: { template_item: product.item_code },
	})
	const data = res.message || {}
	const variants = data.variants || []

	product.attributes = data.attributes || []

	product.variants = variants.map((v) => {
		let cleanName = v.item_name
		if (cleanName.startsWith(product.item_name)) {
			cleanName = cleanName.slice(product.item_name.length).replace(/^[\s-(]+/, "").replace(/\)$/, "")
		}
		return {
			item_code: v.item_code,
			name: cleanName || v.item_name,
			price: v.standard_rate || 0,
			// Don't pre-load per-list prices: keep the editable variant price
			// authoritative on save. The per-variant $ dialog fetches them on open.
			prices: [],
			isExisting: true,
			attributes: v.attributes || {},
			show_bundle: v.enabled_item_bundle === 1,
			disabled: !!v.disabled,
		}
	})
}

// =========================================================================
// Save
// =========================================================================
async function checkItemCodeExists(code) {
	try {
		const res = await frappeCall({ method: "frappe.client.get_value", args: { doctype: "Item", filters: { item_code: code }, fieldname: "name" } })
		return !!(res.message && res.message.name)
	} catch { return false }
}

async function saveVariantItemPrices(variant) {
	const variantCode = variant.item_code
	const variantPrice = variant.price

	let priceEntries = []
	// Use variant-specific prices if set via the per-variant dialog
	if (variant.prices && variant.prices.length > 0) {
		priceEntries = variant.prices.filter(p => p.price_list)
	} else {
		// Build from template-level price list rows:
		// • p.name is set  → row was loaded from DB (first variant's Item Price) → each variant keeps its OWN price
		// • p.name is null → row was ADDED by the user at template level → use the price they typed, apply to all variants
		priceEntries = itemPrices.value.filter((p) => p.price_list).map(p => ({
			price_list: p.price_list,
			price: p.name ? variantPrice : (p.price > 0 ? p.price : (variantPrice || 0))
		}))

		if (priceEntries.length === 0 && priceLists.value.length > 0) {
			priceEntries = [{ price_list: priceLists.value[0].name, price: variantPrice }]
		}
	}

	for (const p of priceEntries) {
		const rate = p.price ?? variantPrice
		const existing = await frappeCall({ method: "frappe.client.get_list", args: { doctype: "Item Price", filters: { item_code: variantCode, price_list: p.price_list, selling: 1 }, fields: ["name"], limit_page_length: 1 } })
		if (existing.message && existing.message.length > 0) {
			await frappeCall({ method: "frappe.client.set_value", args: { doctype: "Item Price", name: existing.message[0].name, fieldname: { price_list_rate: rate } } })
		} else {
			await frappeCall({ method: "frappe.client.insert", args: { doc: { doctype: "Item Price", item_code: variantCode, price_list: p.price_list, price_list_rate: rate, selling: 1 } } })
		}
	}
}

async function saveItemPrices(code) {
	const savedNames = new Set(itemPrices.value.filter(p => p.name).map(p => p.name))
	// Delete entries the user removed
	const allExisting = await frappeCall({
		method: "frappe.client.get_list",
		args: { doctype: "Item Price", filters: { item_code: code, selling: 1 }, fields: ["name"], limit_page_length: 0 }
	})
	for (const ex of (allExisting.message || [])) {
		if (!savedNames.has(ex.name)) {
			await frappeCall({ method: "frappe.client.delete", args: { doctype: "Item Price", name: ex.name } })
		}
	}
	for (const p of itemPrices.value) {
		if (!p.price_list) continue
		if (p.name) {
			await frappeCall({ method: "frappe.client.set_value", args: { doctype: "Item Price", name: p.name, fieldname: { price_list_rate: p.price } } })
		} else {
			await frappeCall({ method: "frappe.client.insert", args: { doc: { doctype: "Item Price", item_code: code, price_list: p.price_list, price_list_rate: p.price, selling: 1 } } })
		}
	}
}

async function saveProduct() {
	if (!product.item_name || !product.item_group) { showMessage(__("\u064A\u062C\u0628 \u0625\u062F\u062E\u0627\u0644 \u0627\u0633\u0645 \u0627\u0644\u0635\u0646\u0641 \u0648\u0627\u0644\u0641\u0626\u0629"), "error"); return }
	saving.value = true
	savingInBackground.value = false
	try {
		if (product.product_type === "standard") {
			if (hasVariants.value) await saveStandardWithVariants()
			else await saveSimpleItem()
		} else { await saveComboItem() }
		if (hasVariants.value && !savingInBackground.value) {
			await bulkSaveVariantPrices()
		} else if (!hasVariants.value) {
			await saveItemPrices(product.item_code)
		}
		if (savingInBackground.value) {
			showMessage(__("\u062C\u0627\u0631\u064D \u0627\u0644\u062D\u0641\u0638 \u0641\u064A \u0627\u0644\u062E\u0644\u0641\u064A\u0629\u2026 \u0633\u064A\u062A\u0645 \u0625\u0634\u0639\u0627\u0631\u0643 \u0639\u0646\u062F \u0627\u0644\u0627\u0646\u062A\u0647\u0627\u0621"))
			// Resolve the background-save UI on EITHER the realtime completion
			// event OR a safety timeout. The POS socket may not be connected /
			// subscribed to the user room, in which case the event never
			// arrives \u2014 we must never leave the editor stuck on an infinite
			// spinner. The variants are still created by the background job and
			// will appear in the list.
			let settled = false
			let timeoutId = null
			const finishBackgroundSave = (data) => {
				if (settled) return
				settled = true
				if (timeoutId) window.clearTimeout(timeoutId)
				try { window.frappe?.realtime?.off?.("variants_save_done", onDone) } catch (e) { /* noop */ }
				if (data && data.success === false) {
					showMessage(data.error || __("\u0641\u0634\u0644 \u0627\u0644\u062D\u0641\u0638 \u0641\u064A \u0627\u0644\u062E\u0644\u0641\u064A\u0629"), "error")
				} else if (data && typeof data.created !== "undefined") {
					showMessage(__("\u062A\u0645 \u062D\u0641\u0638 \u0627\u0644\u0645\u062A\u063A\u064A\u0631\u0627\u062A \u0628\u0646\u062C\u0627\u062D (") + data.created + __(" \u062A\u0645 \u0625\u0646\u0634\u0627\u0624\u0647\u0627)"))
				} else {
					// Timeout fallback: job is still finishing in the background.
					showMessage(__("\u064A\u062A\u0645 \u0625\u0646\u0634\u0627\u0621 \u0627\u0644\u0645\u062A\u063A\u064A\u0631\u0627\u062A \u0641\u064A \u0627\u0644\u062E\u0644\u0641\u064A\u0629 \u0648\u0633\u062A\u0638\u0647\u0631 \u0641\u064A \u0627\u0644\u0642\u0627\u0626\u0645\u0629 \u0628\u0639\u062F \u0642\u0644\u064A\u0644"))
				}
				saving.value = false
				savingInBackground.value = false
				window.setTimeout(() => goBackToList(), 1000)
			}
			const onDone = (data) => finishBackgroundSave(data)
			window.frappe?.realtime?.on?.("variants_save_done", onDone)
			timeoutId = window.setTimeout(() => finishBackgroundSave(null), 12000)
		} else {
			showMessage(__("\u062A\u0645 \u0627\u0644\u062D\u0641\u0638 \u0628\u0646\u062C\u0627\u062D"))
			window.setTimeout(() => goBackToList(), 800)
		}
	} catch (e) { console.error(e); showMessage(e.message || __("\u062E\u0637\u0623 \u0641\u064A \u0627\u0644\u062D\u0641\u0638"), "error") }
	if (!savingInBackground.value) saving.value = false
}

async function saveSimpleItem() {
	if (!product.item_code) throw new Error(__("\u064A\u062C\u0628 \u0625\u062F\u062E\u0627\u0644 \u0643\u0648\u062F \u0627\u0644\u0635\u0646\u0641"))
	if (!isEditing.value && await checkItemCodeExists(product.item_code)) throw new Error(__("\u0643\u0648\u062F \u0627\u0644\u0635\u0646\u0641 \u0645\u0648\u062C\u0648\u062F"))
	const doc = {
		doctype: "Item", item_code: product.item_code, item_name: product.item_name,
		custom_item_name_arabic: product.custom_item_name_arabic, item_group: product.item_group,
		standard_rate: product.standard_rate, image: product.image,
		custom_is_pos_item: product.custom_is_pos_item, custom_fast_sell: product.custom_fast_sell,
		is_stock_item: 0, include_item_in_manufacturing: 0, enabled_item_bundle: 0,
		packaging_delivery: product.packaging_delivery.filter((p) => p.item_code).map((p) => ({ item_code: p.item_code, qty: p.qty })),
		packaging_dinein: product.packaging_dinein.filter((p) => p.item_code).map((p) => ({ item_code: p.item_code, qty: p.qty })),
		packaging_takeaway: product.packaging_takeaway.filter((p) => p.item_code).map((p) => ({ item_code: p.item_code, qty: p.qty })),
		custom_addons: product.addons.filter((a) => a.item_code),
		custom_addons_label: product.addons_label || "",
	}
	if (isEditing.value) {
		await frappeCall({ method: "frappe.client.set_value", args: { doctype: "Item", name: product.item_code, fieldname: doc } })
	} else {
		await frappeCall({ method: "frappe.client.insert", args: { doc } })
	}
}

async function saveStandardWithVariants() {
	if (!isEditing.value) {
		if (!product.item_code) throw new Error(__("\u064A\u062C\u0628 \u0625\u062F\u062E\u0627\u0644 \u0643\u0648\u062F"))
		if (await checkItemCodeExists(product.item_code)) throw new Error(__("\u0643\u0648\u062F \u0645\u0648\u062C\u0648\u062F"))
	}

	if (product.attributes.length === 0 && product.variants.length > 0) {
		product.attributes.push({ attribute: "Type", values: product.variants.map((v) => v.name).filter(Boolean) })
		product.variants.forEach((v) => { v.attributes = [{ attribute: "Type", value: v.name }] })
	}

	for (const attr of product.attributes) await ensureAttributeExists(attr.attribute, attr.values)

	const packagingPayload = {
		packaging_delivery: product.packaging_delivery.filter((p) => p.item_code).map((p) => ({ item_code: p.item_code, qty: p.qty })),
		packaging_dinein: product.packaging_dinein.filter((p) => p.item_code).map((p) => ({ item_code: p.item_code, qty: p.qty })),
		packaging_takeaway: product.packaging_takeaway.filter((p) => p.item_code).map((p) => ({ item_code: p.item_code, qty: p.qty })),
	}
	if (!isEditing.value) {
		const tplDoc = {
			doctype: "Item", item_code: product.item_code, item_name: product.item_name,
			custom_item_name_arabic: product.custom_item_name_arabic, item_group: product.item_group,
			image: product.image, custom_is_pos_item: product.custom_is_pos_item,
			custom_fast_sell: product.custom_fast_sell, has_variants: 1, is_stock_item: 0,
			stock_uom: "Unit", include_item_in_manufacturing: 0,
			attributes: product.attributes.map((a) => ({ attribute: a.attribute })),
			custom_addons: product.addons.filter((a) => a.item_code),
			custom_addons_label: product.addons_label || "",
			...packagingPayload,
		}
		const res = await frappeCall({ method: "frappe.client.insert", args: { doc: tplDoc } })
		product.item_code = res.message.item_code
	} else {
		await frappeCall({ method: "frappe.client.set_value", args: { doctype: "Item", name: product.item_code, fieldname: { custom_addons: product.addons.filter((a) => a.item_code), custom_addons_label: product.addons_label || "", ...packagingPayload } } })
	}

	// Separate existing vs new variants
	const existingToUpdate = []
	const newVariants = []
	for (const v of product.variants) {
		if (!v.name) continue
		if (v.isExisting) {
			existingToUpdate.push({ item_code: v.item_code, price: v.price, disabled: v.disabled ? 1 : 0 })
		} else {
			if (!v.attributes || !v.attributes.length) v.attributes = [{ attribute: "Type", value: v.name }]
			if (!v.item_code) throw new Error(__("\u064A\u062C\u0628 \u0625\u062F\u062E\u0627\u0644 \u0643\u0648\u062F \u0627\u0644\u0645\u062A\u063A\u064A\u0631"))
			newVariants.push({
				item_code: v.item_code,
				name: v.name,
				price: v.price,
				attributes: v.attributes.map((a) => ({ attribute: a.attribute, value: a.value })),
			})
		}
	}

	// Enqueue new variant creation as a background job (returns immediately)
	if (newVariants.length > 0) {
		const templatePrices = itemPrices.value.filter(p => p.price_list).map(p => ({
			price_list: p.price_list,
			price: p.name ? null : (p.price > 0 ? p.price : null),  // null = use variant's own price
		}))
		await frappeCall({
			method: "ecs_posnext.api.item_manager.bulk_create_variants",
			args: {
				template_code: product.item_code,
				variants: newVariants,
				template_name: product.item_name,
				template_name_arabic: product.custom_item_name_arabic || "",
				item_group: product.item_group,
				prices: templatePrices,
			},
		})
		savingInBackground.value = true
	}

	// Bulk-update existing variant rates synchronously (fast, no new variants needed)
	if (existingToUpdate.length > 0) {
		await frappeCall({
			method: "ecs_posnext.api.item_manager.bulk_update_variant_rates",
			args: { variants: existingToUpdate },
		})
	}
}

async function bulkSaveVariantPrices() {
	const entries = []
	// Target price lists = every list shown in the Prices section (fallback: default).
	let targetLists = itemPrices.value.filter((p) => p.price_list).map((p) => p.price_list)
	if (targetLists.length === 0 && priceLists.value.length > 0) targetLists = [priceLists.value[0].name]
	targetLists = [...new Set(targetLists)]

	for (const v of product.variants) {
		if (!v.item_code) continue
		const variantPrice = Number(v.price) || 0
		// Explicit per-variant per-list prices (set via the $ dialog) take priority.
		const explicit = (v.prices || []).filter((p) => p.price_list)
		if (explicit.length > 0) {
			for (const p of explicit) {
				entries.push({ item_code: v.item_code, price_list: p.price_list, price: Number(p.price ?? variantPrice) || 0 })
			}
		} else {
			// Each variant's own price → every target price list.
			for (const pl of targetLists) {
				entries.push({ item_code: v.item_code, price_list: pl, price: variantPrice })
			}
		}
	}
	if (entries.length === 0) return
	await frappeCall({
		method: "ecs_posnext.api.item_manager.bulk_upsert_item_prices",
		args: { entries },
	})
}

// =========================================================================
// Variant Prices Dialog
// =========================================================================
async function openVariantPricesDialog(variant) {
	currentVariantForPrices.value = variant
	currentVariantPrices.value = []

	if (variant.isExisting && variant.prices && variant.prices.length > 0) {
		currentVariantPrices.value = variant.prices.map(p => ({ ...p }))
	} else if (variant.isExisting) {
		const res = await frappeCall({
			method: "frappe.client.get_list",
			args: {
				doctype: "Item Price",
				fields: ["name", "price_list", "price_list_rate"],
				filters: { item_code: variant.item_code, selling: 1 },
				limit_page_length: 0
			}
		})
		currentVariantPrices.value = (res.message || []).map(p => ({
			name: p.name,
			price_list: p.price_list,
			price: p.price_list_rate
		}))
		variant.prices = [...currentVariantPrices.value]
	} else {
		currentVariantPrices.value = (variant.prices || []).map(p => ({ ...p }))
	}
	
	if (currentVariantPrices.value.length === 0 && priceLists.value.length > 0) {
		addVariantPriceRow()
	}
	
	showVariantPricesDialog.value = true
}

function addVariantPriceRow() {
	const defaultPrice = currentVariantForPrices.value?.price || 0
	currentVariantPrices.value.push({ price_list: priceLists.value[0]?.name || "", price: defaultPrice })
}

function removeVariantPriceRow(idx) {
	currentVariantPrices.value.splice(idx, 1)
}

async function saveVariantPrices() {
	if (!currentVariantForPrices.value) return
	
	if (currentVariantForPrices.value.isExisting) {
		saving.value = true
		try {
			// Delete existing
			const existing = await frappeCall({
				method: "frappe.client.get_list",
				args: { doctype: "Item Price", filters: { item_code: currentVariantForPrices.value.item_code, selling: 1 }, fields: ["name"] }
			})
			for (const p of (existing.message || [])) {
				await frappeCall({ method: "frappe.client.delete", args: { doctype: "Item Price", name: p.name } })
			}
			// Insert new
			for (const p of currentVariantPrices.value) {
				if (!p.price_list) continue
				await frappeCall({
					method: "frappe.client.insert",
					args: {
						doc: {
							doctype: "Item Price",
							item_code: currentVariantForPrices.value.item_code,
							price_list: p.price_list,
							price_list_rate: p.price,
							selling: 1
						}
					}
				})
			}
			showMessage(__("تم حفظ أسعار المتغير بنجاح"))
		} catch (e) {
			console.error(e)
			showMessage(e.message || __("خطأ في حفظ الأسعار"), "error")
		}
		saving.value = false
	} else {
		currentVariantForPrices.value.prices = currentVariantPrices.value.map(p => ({ ...p }))
	}
	showVariantPricesDialog.value = false
}

// =========================================================================
// Extra Prices Dialog (Combo)
// =========================================================================
function openExtraPricesDialog(option) {
	currentOptionForExtraPrices.value = option
	if (!option.extra_prices) option.extra_prices = []
	currentExtraPrices.value = (option.extra_prices || []).map(p => ({ ...p }))
	
	if (currentExtraPrices.value.length === 0 && priceLists.value.length > 0) {
		addExtraPriceRow()
	}
	showExtraPricesDialog.value = true
}

function addExtraPriceRow() {
	const defaultPrice = currentOptionForExtraPrices.value?.extra_price || 0
	currentExtraPrices.value.push({ price_list: priceLists.value[0]?.name || "", price: defaultPrice })
}

function removeExtraPriceRow(idx) {
	currentExtraPrices.value.splice(idx, 1)
}

function saveExtraPrices() {
	if (!currentOptionForExtraPrices.value) return
	currentOptionForExtraPrices.value.extra_prices = currentExtraPrices.value.filter(p => p.price_list)
	// Also set the base extra_price to the first price if available for backward compatibility
	if (currentOptionForExtraPrices.value.extra_prices.length > 0) {
		currentOptionForExtraPrices.value.extra_price = currentOptionForExtraPrices.value.extra_prices[0].price
	}
	showExtraPricesDialog.value = false
}



function _uniqueAbbr(value, usedAbbrs) {
	let base = value.replace(/[^A-Za-z0-9]/g, "").toUpperCase()
	// Non-Latin values (e.g. Arabic) strip down to an empty base — fall back to
	// a safe placeholder so we still produce a usable, unique abbreviation
	// instead of looping forever.
	if (!base) base = "V"
	// Try lengths 2, 3, 4 … up to the base length, then append a counter.
	for (let len = 2; len <= base.length; len++) {
		const candidate = base.substring(0, len)
		if (!usedAbbrs.has(candidate)) { usedAbbrs.add(candidate); return candidate }
	}
	// All prefix lengths collide — append a numeric suffix
	let i = 1
	while (true) {
		const candidate = base.substring(0, 3) + i
		if (!usedAbbrs.has(candidate)) { usedAbbrs.add(candidate); return candidate }
		i++
	}
}

async function ensureAttributeExists(name, values) {
	const chk = await frappeCall({ method: "frappe.client.get_value", args: { doctype: "Item Attribute", filters: { name }, fieldname: "name" } })
	const exists = !!(chk.message && chk.message.name)
	if (!exists) {
		const usedAbbrs = new Set()
		await frappeCall({ method: "frappe.client.insert", args: { doc: { doctype: "Item Attribute", attribute_name: name, item_attribute_values: values.map((v) => ({ attribute_value: v, abbr: _uniqueAbbr(v, usedAbbrs) })) } } })
	} else {
		const d = await frappeCall({ method: "frappe.client.get", args: { doctype: "Item Attribute", name } })
		const ev = (d.message.item_attribute_values || []).map((v) => v.attribute_value)
		const nv = values.filter((v) => !ev.includes(v))
		if (nv.length) {
			const doc = d.message
			// Seed usedAbbrs from already-saved values to avoid clashing with them
			const usedAbbrs = new Set((doc.item_attribute_values || []).map((v) => v.abbr))
			for (const v of nv) doc.item_attribute_values.push({ attribute_value: v, abbr: _uniqueAbbr(v, usedAbbrs) })
			await frappeCall({ method: "frappe.client.save", args: { doc } })
		}
	}
}

async function saveComboItem() {
	const components = []
	for (const sec of product.sections) {
		for (const opt of sec.options) {
			if (opt.has_variants && opt.variants) {
				for (const vr of opt.variants) {
					if (vr.item_code) {
						const ep = JSON.stringify(vr.extra_prices || [])
						const la = JSON.stringify(opt.locked_attributes || [])
						components.push({ section_name: sec.name, section_type: sec.section_type || "Component", is_required: sec.is_required ? 1 : 0, item_code: vr.item_code, min_qty: sec.min_qty || 0, max_qty: sec.max_qty || 1, default_selected: vr.default_selected ? 1 : 0, extra_price: vr.extra_price || 0, extra_prices: ep, qty: opt.qty || vr.qty || 1, is_standalone: 0, locked_attributes: la, lock_group: vr.lock_group || "" })
					}
				}
			} else if (opt.item_code) {
				const ep = JSON.stringify(opt.extra_prices || [])
				components.push({ section_name: sec.name, section_type: sec.section_type || "Component", is_required: sec.is_required ? 1 : 0, item_code: opt.item_code, min_qty: sec.min_qty || 0, max_qty: sec.max_qty || 1, default_selected: opt.default_selected ? 1 : 0, extra_price: opt.extra_price || 0, extra_prices: ep, qty: opt.qty || 1, is_standalone: 1 })
			}
		}
	}
	if (!product.item_code) throw new Error(__("\u064A\u062C\u0628 \u0625\u062F\u062E\u0627\u0644 \u0643\u0648\u062F"))
	if (!isEditing.value && await checkItemCodeExists(product.item_code)) throw new Error(__("\u0643\u0648\u062F \u0645\u0648\u062C\u0648\u062F"))
	const doc = {
		doctype: "Item", item_code: product.item_code, item_name: product.item_name,
		custom_item_name_arabic: product.custom_item_name_arabic, item_group: product.item_group,
		standard_rate: product.standard_rate, image: product.image,
		custom_is_pos_item: product.custom_is_pos_item, custom_fast_sell: product.custom_fast_sell,
		is_stock_item: 0, include_item_in_manufacturing: 0, enabled_item_bundle: 1,
		combo_components: components,
		packaging_delivery: product.packaging_delivery.filter((p) => p.item_code).map((p) => ({ item_code: p.item_code, qty: p.qty })),
		packaging_dinein: product.packaging_dinein.filter((p) => p.item_code).map((p) => ({ item_code: p.item_code, qty: p.qty })),
		packaging_takeaway: product.packaging_takeaway.filter((p) => p.item_code).map((p) => ({ item_code: p.item_code, qty: p.qty })),
	}
	if (isEditing.value) {
		await frappeCall({ method: "frappe.client.set_value", args: { doctype: "Item", name: product.item_code, fieldname: doc } })
	} else {
		await frappeCall({ method: "frappe.client.insert", args: { doc } })
	}
}

async function fetchPriceLists() {
	try {
		const res = await frappeCall({ method: "frappe.client.get_list", args: { doctype: "Price List", fields: ["name"], filters: { enabled: 1, selling: 1 }, limit_page_length: 0 } })
		// Hide the "El Menus" price list from the product editor selectors.
		priceLists.value = (res.message || []).filter((pl) => (pl.name || "").trim().toLowerCase() !== "el menus")
	} catch (e) { console.error(e) }
}

// =========================================================================
// Lifecycle
// =========================================================================
onMounted(() => { loadData(); fetchPriceLists() })
</script>

<style scoped>
.form-input{@apply w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:text-gray-500}
.form-lbl{@apply block text-[11px] font-semibold text-gray-500 uppercase tracking-wide mb-1}
.toggle-cb{@apply w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500}
.tbl-th{@apply bg-[#f8f9fc] text-[#8a94a6] font-semibold text-[11px] uppercase tracking-wider py-3.5 px-3 whitespace-nowrap}
.tbl-td{@apply py-3.5 px-3 text-sm text-[#3a3a4a] align-middle}
</style>
