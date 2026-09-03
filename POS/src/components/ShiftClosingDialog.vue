<template>
  <Dialog v-model="open" :options="{ title: __('Close POS Shift'), size: '4xl' }">
    <template #body-content>
      <div class="flex flex-col gap-3 md:gap-6">
        <div v-if="isLoadingData" class="text-center py-8 md:py-12">
          <div class="inline-block animate-spin rounded-full h-12 w-12 md:h-16 md:w-16 border-b-4 border-blue-600">
          </div>
          <p class="mt-3 md:mt-4 text-base md:text-lg font-medium text-gray-600">{{ __('Loading shift data...') }}</p>
          <p class="text-xs md:text-sm text-gray-500">{{ __('Calculating totals and reconciliation...') }}</p>
        </div>

        <div v-else-if="closingData" class="flex flex-col gap-3 md:gap-6">
          <!-- Shift Summary Header (hidden in entry mode when hideExpectedAmount is enabled) -->
          <div v-if="shouldShowSummary" class="bg-white border border-gray-200 rounded-lg p-3 md:p-6 shadow-sm">
            <div class="flex flex-col sm:flex-row justify-start items-start gap-3 mb-3 md:mb-6">
              <div class="flex-1">
                <h3 class="text-start text-sm md:text-base font-medium text-gray-900">{{ closingData.pos_profile }}</h3>
                <p class="text-start text-xs md:text-sm text-gray-500 mt-1">{{
                  formatDateTime(closingData.period_start_date) }}</p>
              </div>
              <div class="text-start sm:text-end">
                <div class="text-start text-xs text-gray-500 uppercase">{{ __('Duration') }}</div>
                <div class="text-base md:text-lg font-semibold text-gray-900">{{ getShiftDuration() }}</div>
              </div>
            </div>

            <!-- Key Metrics Grid -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-4">
              <!-- Gross Sales (before returns) -->
              <div class="text-start bg-blue-50 border border-blue-200 rounded-lg p-3 md:p-4">
                <div class="text-blue-600 text-xs uppercase font-medium mb-1">{{ __('Gross Sales') }}</div>
                <div class="text-lg md:text-2xl font-bold text-blue-900 mb-0.5 md:mb-1 truncate">{{
                  formatCurrency(grossSales) }}</div>
                <div class="text-blue-600 text-xs">{{ __('{0} invoices', [closingData.sales_count || salesInvoiceCount])
                  }}</div>
              </div>

              <!-- Returns -->
              <div v-if="hasReturns" class="text-start bg-red-50 border border-red-200 rounded-lg p-3 md:p-4">
                <div class="text-red-600 text-xs uppercase font-medium mb-1">{{ __('Returns') }}</div>
                <div class="text-lg md:text-2xl font-bold text-red-700 mb-0.5 md:mb-1 truncate">-{{
                  formatCurrency(closingData.returns_total) }}</div>
                <div class="text-red-600 text-xs">{{ __('{0} returns', [closingData.returns_count]) }}</div>
              </div>

              <!-- Net Sales (after returns) -->
              <div class="text-start bg-green-50 border border-green-200 rounded-lg p-3 md:p-4">
                <div class="text-green-600 text-xs uppercase font-medium mb-1">{{ __('Net Sales') }}</div>
                <div class="text-lg md:text-2xl font-bold text-green-900 mb-0.5 md:mb-1 truncate">{{
                  formatCurrency(closingData.grand_total) }}</div>
                <div class="text-green-600 text-xs">{{ __('After returns') }}</div>
              </div>

              <!-- Tax Collected -->
              <div class="text-start bg-gray-50 border border-gray-200 rounded-lg p-3 md:p-4">
                <div class="text-gray-600 text-xs uppercase font-medium mb-1">{{ __('Tax Collected') }}</div>
                <div class="text-lg md:text-2xl font-bold text-gray-900 mb-0.5 md:mb-1 truncate">{{
                  formatCurrency(totalTax) }}</div>
                <div class="text-gray-600 text-xs">{{ __('Net tax') }}</div>
              </div>
            </div>
          </div>

          <!-- No Sales Warning (hidden in entry mode when hideExpectedAmount is enabled) -->
          <div v-if="shouldShowSummary && invoiceCount === 0"
            class="bg-yellow-50 border border-yellow-200 rounded-lg p-3 md:p-4">
            <div class="flex items-start gap-2 md:gap-3">
              <div class="flex-shrink-0">
                <svg class="h-4 w-4 md:h-5 md:w-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    clip-rule="evenodd" />
                </svg>
              </div>
              <div>
                <h3 class="text-xs md:text-sm font-medium text-yellow-900">{{ __('No Sales During This Shift') }}</h3>
                <p class="text-xs md:text-sm text-yellow-700 mt-1 md:mt-2">
                  {{ __('No invoices were created. Closing amounts should match opening amounts.') }}
                </p>
              </div>
            </div>
          </div>

          <!-- Invoice Details (Collapsible) (hidden in entry mode when hideExpectedAmount is enabled) -->
          <div v-if="shouldShowSummary && invoiceCount > 0"
            class="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
            <button @click="showInvoiceDetails = !showInvoiceDetails"
              :aria-label="`${showInvoiceDetails ? 'Hide' : 'Show'} invoice details for ${invoiceCount} transactions`"
              :aria-expanded="showInvoiceDetails"
              class="w-full px-3 py-3 md:px-6 md:py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
              <div class="text-start">
                <h3 class="text-sm md:text-lg font-medium text-gray-900">{{ __('Invoice Details') }}</h3>
                <p class="text-xs md:text-sm text-gray-500">{{ __('{0} transactions • {1}', [
                  invoiceCount,
                  formatCurrency(closingData.grand_total)
                ]) }}</p>
              </div>
              <svg
                :class="['h-4 w-4 md:h-5 md:w-5 text-gray-400 transition-transform', showInvoiceDetails ? 'transform rotate-180' : '']"
                fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            <div v-show="showInvoiceDetails" class="border-t border-gray-200">
              <!-- Mobile Card View -->
              <div class="md:hidden divide-y divide-gray-200">
                <div v-for="(invoice, idx) in closingData.pos_transactions" :key="idx"
                  :class="['p-3', invoice.is_return ? 'bg-red-50 hover:bg-red-100' : 'hover:bg-gray-50']">
                  <div class="flex justify-between items-start mb-2">
                    <div class="flex items-center gap-2">
                      <span :class="['text-xs font-medium', invoice.is_return ? 'text-red-700' : 'text-gray-900']">
                        {{ invoice.pos_invoice || invoice.sales_invoice || __('N/A') }}
                      </span>
                      <span v-if="invoice.is_return"
                        class="px-1.5 py-0.5 text-xs font-medium bg-red-200 text-red-800 rounded">
                        {{ __('Return') }}
                      </span>
                    </div>
                    <span :class="['text-sm font-semibold', invoice.is_return ? 'text-red-700' : 'text-gray-900']">
                      {{ formatCurrency(invoice.grand_total) }}
                    </span>
                  </div>
                  <div class="flex justify-between items-center text-xs text-gray-600">
                    <span>{{ invoice.customer }}</span>
                    <span class="text-gray-500">{{ formatTime(invoice.posting_date) }}</span>
                  </div>
                </div>
                <div class="bg-gray-50 p-3">
                  <div class="flex justify-between items-center">
                    <span class="text-xs font-semibold text-gray-700">{{ __('Net Total:') }}</span>
                    <span class="text-sm font-bold text-gray-900">
                      {{ formatCurrency(closingData.grand_total) }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Desktop Table View -->
              <div class="hidden md:block overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-gray-50">
                    <tr>
                      <th class="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase">{{ __('Invoice') }}
                      </th>
                      <th class="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase">{{ __('Type') }}</th>
                      <th class="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase">{{ __('Customer') }}
                      </th>
                      <th class="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase">{{ __('Time') }}</th>
                      <th class="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase">{{ __('Amount') }}
                      </th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-for="(invoice, idx) in closingData.pos_transactions" :key="idx"
                      :class="invoice.is_return ? 'bg-red-50 hover:bg-red-100' : 'hover:bg-gray-50'">
                      <td class="text-start px-6 py-4 whitespace-nowrap">
                        <span :class="['text-sm font-medium', invoice.is_return ? 'text-red-700' : 'text-gray-900']">
                          {{ invoice.pos_invoice || invoice.sales_invoice || __('N/A') }}
                        </span>
                      </td>
                      <td class="text-start px-6 py-4 whitespace-nowrap">
                        <span v-if="invoice.is_return"
                          class="px-2 py-1 text-xs font-medium bg-red-200 text-red-800 rounded">
                          {{ __('Return') }}
                        </span>
                        <span v-else class="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">
                          {{ __('Sale') }}
                        </span>
                      </td>
                      <td class="text-start px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {{ invoice.customer }}
                      </td>
                      <td class="text-start px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {{ formatTime(invoice.posting_date) }}
                      </td>
                      <td class="text-start px-6 py-4 whitespace-nowrap">
                        <span :class="['text-sm font-semibold', invoice.is_return ? 'text-red-700' : 'text-gray-900']">
                          {{ formatCurrency(invoice.grand_total) }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                  <tfoot class="bg-gray-50">
                    <tr>
                      <td colspan="4" class="px-6 py-4 text-start text-sm font-semibold text-gray-700">
                        {{ __('Net Total:') }}
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-start">
                        <span class="text-base font-bold text-gray-900">
                          {{ formatCurrency(closingData.grand_total) }}
                        </span>
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          </div>

          <!-- Payment Reconciliation -->
          <div class="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
            <div :class="[
              'px-3 py-3 md:px-6 md:py-4 border-b border-gray-200',
              hideExpectedAmount && showSuccessReport ? 'bg-green-50 border-green-200' : 'bg-gray-50'
            ]">
              <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                <div>
                  <div class="text-start flex items-center gap-2">
                    <h3 class="text-sm md:text-lg font-semibold text-gray-900">{{ __('Payment Reconciliation') }}</h3>
                    <span v-if="hideExpectedAmount && showSuccessReport"
                      class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      {{ __('✓ Shift Closed') }}
                    </span>
                  </div>
                  <p class="text-xs md:text-sm text-gray-600">
                    {{ reconciliationMessage }}
                  </p>
                </div>
                <div v-if="shouldShowSummary && getTotalDifference !== 0" class="text-start sm:text-end">
                  <div class="text-xs mb-1 text-gray-500 uppercase">{{ __('Total Variance') }}</div>
                  <div :class="[
                    'text-lg md:text-xl font-bold',
                    getTotalDifference > 0 ? 'text-blue-600' : 'text-red-600'
                  ]">
                    {{ getTotalDifference > 0 ? '+' : '' }}{{ formatCurrency(Math.abs(getTotalDifference)) }}
                  </div>
                </div>
              </div>
            </div>

            <div class="p-3 md:p-6">
              <!-- ENTRY MODE: Simple blind input list (when hideExpectedAmount is enabled and not showing report) -->
              <div v-if="isInEntryMode" class="flex flex-col gap-3 md:gap-4">
                <div v-for="(payment, idx) in closingData.payment_reconciliation" :key="idx"
                  class="border border-gray-200 rounded-lg p-3 md:p-4 bg-white hover:border-gray-300 transition-colors">
                  <div class="flex items-center justify-between gap-3">
                    <!-- Payment Method Name with Icon -->
                    <div class="flex items-center gap-2 md:gap-3 flex-1">
                      <div
                        :class="['rounded-lg p-1.5 md:p-2 flex-shrink-0', getPaymentIcon(payment.mode_of_payment).color]">
                        <span class="text-base md:text-xl">{{ getPaymentIcon(payment.mode_of_payment).icon }}</span>
                      </div>
                      <label :for="`payment-${idx}`"
                        class="text-start text-sm md:text-base font-semibold text-gray-900 cursor-pointer">
                        {{ payment.mode_of_payment }}
                      </label>
                    </div>

                    <!-- Simple Input with Native Arrows -->
                    <div class="w-40 md:w-48">
                      <Input :id="`payment-${idx}`" :modelValue="payment.closing_amount"
                        @update:modelValue="(value) => updateClosingAmount(payment, value)" type="number" step="10"
                        min="0" placeholder="0.00" :disabled="isSubmitting"
                        :aria-label="__('Enter actual amount for {0}', [payment.mode_of_payment])"
                        :aria-invalid="isZeroClosingAmount(payment)"
                        class="text-base md:text-lg text-center font-semibold" />
                      <p v-if="isZeroClosingAmount(payment)" class="text-xs text-red-600 mt-1 text-center">
                        {{ __('Amount cannot be 0') }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- REVIEW MODE: Full payment method cards (when not in entry mode) -->
              <div v-else class="flex flex-col gap-4 md:gap-5">
                <div v-for="(payment, idx) in closingData.payment_reconciliation" :key="idx" :class="[
                  'border rounded-lg p-3 md:p-5 transition-all',
                  payment.difference === 0 ? 'border-green-200 bg-green-50' :
                    payment.difference > 0 ? 'border-blue-200 bg-blue-50' :
                      'border-red-200 bg-red-50'
                ]">
                  <div class="flex items-start justify-between mb-3 md:mb-4 gap-2">
                    <div class="flex items-center gap-2 md:gap-3">
                      <!-- Payment Method Icon -->
                      <div :class="['rounded-lg p-1.5 md:p-2', getPaymentIcon(payment.mode_of_payment).color]">
                        <span class="text-base md:text-xl">{{ getPaymentIcon(payment.mode_of_payment).icon }}</span>
                      </div>
                      <div>
                        <h4 class="text-start text-sm md:text-base font-semibold text-gray-900">{{
                          payment.mode_of_payment }}</h4>
                        <TranslatedHTML :tag="'p'" class="text-xs md:text-sm text-gray-600"
                          :inner="__('Expected: &lt;span class=&quot;font-medium&quot;&gt;{0}&lt;/span&gt;', [formatCurrency(payment.expected_amount)])" />
                      </div>
                    </div>

                    <!-- Status Badge -->
                    <div v-if="payment.closing_amount !== null && payment.closing_amount !== undefined"
                      class="flex-shrink-0">
                      <span v-if="payment.difference === 0"
                        class="inline-flex items-center px-2 md:px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        {{ __('✓ Balanced') }}
                      </span>
                      <span v-else-if="payment.difference > 0"
                        class="inline-flex items-center px-2 md:px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {{ __('Over {0}', [formatCurrency(payment.difference)]) }}
                      </span>
                      <span v-else
                        class="inline-flex items-center px-2 md:px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        {{ __('Short {0}', [formatCurrency(Math.abs(payment.difference))]) }}
                      </span>
                    </div>
                  </div>

                  <!-- Amount Entry Grid -->
                  <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 md:gap-3">
                    <!-- Opening Amount -->
                    <div class="text-start bg-white rounded-lg p-2 md:p-3 border border-gray-200">
                      <label class="block text-xs font-medium text-gray-500 uppercase mb-0.5 md:mb-1">{{ __('Opening')
                        }}</label>
                      <div class="text-base md:text-lg font-semibold text-gray-900">
                        {{ formatCurrency(payment.opening_amount) }}
                      </div>
                      <div class="text-xs text-gray-500 mt-0.5 md:mt-1 hidden sm:block">{{ __('Shift start') }}</div>
                    </div>

                    <!-- Expected Amount -->
                    <div class="text-start bg-white rounded-lg p-2 md:p-3 border border-gray-200">
                      <label class="block text-xs font-medium text-gray-500 uppercase mb-0.5 md:mb-1">{{ __('Expected')
                        }}</label>
                      <div class="text-base md:text-lg font-semibold text-gray-900">
                        {{ formatCurrency(payment.expected_amount) }}
                      </div>
                      <div class="text-xs text-gray-500 mt-0.5 md:mt-1 hidden sm:block">
                        <span v-if="getSalesForPayment(payment) > 0">
                          +{{ formatCurrency(getSalesForPayment(payment)) }}
                        </span>
                        <span v-else>{{ __('No sales') }}</span>
                      </div>
                    </div>

                    <!-- Actual/Closing Amount -->
                    <div class="text-start bg-white rounded-lg p-2 md:p-3 border border-gray-300">
                      <label class="block text-xs font-medium text-gray-700 uppercase mb-0.5 md:mb-1">
                        {{ __('Actual Amount *') }}
                      </label>
                      <Input :modelValue="payment.closing_amount"
                        @update:modelValue="(value) => updateClosingAmount(payment, value)" type="number" step="0.01"
                        min="0" placeholder="0.00" :disabled="showSuccessReport || isSubmitting"
                        :aria-label="`Enter actual amount for ${payment.mode_of_payment}`"
                        :aria-invalid="!showSuccessReport && isZeroClosingAmount(payment)"
                        class="text-base md:text-lg" />
                      <p v-if="!showSuccessReport && isZeroClosingAmount(payment)"
                        class="text-xs text-red-600 mt-0.5 md:mt-1 font-medium">
                        {{ __('Amount cannot be 0') }}
                      </p>
                      <div v-else class="text-xs text-gray-500 mt-0.5 md:mt-1 hidden sm:block">
                        {{ showSuccessReport ? __('Final Amount') : __('Count & enter') }}
                      </div>
                    </div>
                  </div>

                  <!-- Difference Alert -->
                  <div
                    v-if="payment.closing_amount !== null && payment.closing_amount !== undefined && payment.difference !== 0"
                    class="text-start mt-2 md:mt-3 p-2 md:p-3 rounded-lg" :class="[
                      payment.difference > 0 ? 'bg-blue-50 border border-blue-200' : 'bg-red-50 border border-red-200'
                    ]">
                    <div class="flex items-center justify-between gap-2">
                      <div class="flex-1">
                        <p
                          :class="['text-xs md:text-sm font-medium', payment.difference > 0 ? 'text-blue-900' : 'text-red-900']">
                          {{ payment.difference > 0 ? __('Cash Over') : __('Cash Short') }}
                        </p>
                        <p :class="['text-xs', payment.difference > 0 ? 'text-blue-700' : 'text-red-700']">
                          {{ payment.difference > 0
                            ? __('You have more than expected.')
                            : __('You have less than expected.')
                          }}
                        </p>
                      </div>
                      <div
                        :class="['text-base md:text-xl font-bold', payment.difference > 0 ? 'text-blue-700' : 'text-red-700']">
                        {{ payment.difference > 0 ? '+' : '' }}{{ formatCurrency(payment.difference) }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Reconciliation Summary (hidden in entry mode when hideExpectedAmount is enabled) -->
            <div v-if="shouldShowSummary"
              class="text-start bg-gray-50 px-3 py-3 md:px-6 md:py-4 border-t border-gray-200">
              <div class="grid grid-cols-3 gap-2 md:gap-4">
                <div>
                  <p class="text-xs md:text-sm text-gray-600">{{ __('Total Expected') }}</p>
                  <p class="text-base md:text-xl font-semibold text-gray-900">{{ formatCurrency(getTotalExpected) }}</p>
                </div>
                <div>
                  <p class="text-xs md:text-sm text-gray-600">{{ __('Total Actual') }}</p>
                  <p class="text-base md:text-xl font-semibold text-gray-900">{{ formatCurrency(getTotalActual) }}</p>
                </div>
                <div>
                  <p class="text-xs md:text-sm text-gray-600">{{ __('Net Variance') }}</p>
                  <p :class="[
                    'text-base md:text-xl font-bold',
                    getTotalDifference === 0 ? 'text-green-600' :
                      getTotalDifference > 0 ? 'text-blue-600' : 'text-red-600'
                  ]">
                    {{ getTotalDifference === 0 ? '✓ ' : getTotalDifference > 0 ? '+' : '' }}{{
                      formatCurrency(Math.abs(getTotalDifference)) }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- Tax Summary (hidden in entry mode when hideExpectedAmount is enabled) -->
          <div v-if="shouldShowSummary && closingData.taxes && closingData.taxes.length > 0"
            class="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
            <div class="px-3 py-3 md:px-6 md:py-4 bg-gray-50 border-b border-gray-200">
              <h3 class="text-sm md:text-lg font-medium text-gray-900">{{ __('Tax Summary') }}</h3>
            </div>
            <div class="p-3 md:p-6">
              <div class="flex flex-col gap-2 md:gap-3">
                <div v-for="(tax, idx) in closingData.taxes" :key="idx"
                  class="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                  <div>
                    <p class="text-xs md:text-sm font-medium text-gray-900">{{ tax.account_head }}</p>
                    <p class="text-xs text-gray-500">{{ formatQuantity(tax.rate) }}%</p>
                  </div>
                  <div class="text-end">
                    <p class="text-sm md:text-base font-semibold text-gray-900">{{ formatCurrency(tax.amount) }}</p>
                  </div>
                </div>
              </div>
              <div class="mt-3 md:mt-4 pt-3 md:pt-4 border-t border-gray-200">
                <div class="flex items-center justify-between">
                  <span class="text-xs md:text-sm font-medium text-gray-700">{{ __('Total Tax Collected') }}</span>
                  <span class="text-base md:text-lg font-bold text-gray-900">{{ formatCurrency(totalTax) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Error Display -->
          <div v-if="submitResource.error || (errorMessage && !closingDataResource.error)"
            class="rounded-lg bg-red-50 border border-red-200 p-3 md:p-4">
            <div class="flex gap-2 md:gap-3">
              <svg class="h-4 w-4 md:h-5 md:w-5 text-red-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clip-rule="evenodd" />
              </svg>
              <div class="flex-1">
                <h4 class="text-xs md:text-sm font-medium text-red-800">{{ __('Error Closing Shift') }}</h4>
                <p class="text-xs md:text-sm text-red-700 mt-1">{{ errorMessage || submitResource.error }}</p>
                <button v-if="errorMessage" @click="errorMessage = ''"
                  class="mt-2 text-xs text-red-600 hover:text-red-800 underline">
                  {{ __('Dismiss') }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Error State -->
        <div v-else-if="closingDataResource.error || errorMessage"
          class="rounded-lg bg-red-50 border border-red-200 p-3 md:p-4">
          <div class="flex gap-2 md:gap-3">
            <svg class="h-4 w-4 md:h-5 md:w-5 text-red-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clip-rule="evenodd" />
            </svg>
            <div>
              <h3 class="text-xs md:text-sm font-medium text-red-800">{{ __('Failed to Load Shift Data') }}</h3>
              <p class="text-xs md:text-sm text-red-700 mt-1">{{ errorMessage || closingDataResource.error }}</p>
            </div>
          </div>
        </div>
      </div>
    </template>

    <template #actions>
      <div class="flex flex-col sm:flex-row justify-between w-full items-stretch sm:items-center gap-2 sm:gap-0">
        <!-- Left side - Cancel/Close button -->
        <Button variant="subtle" @click="closeDialog" :disabled="isSubmitting" class="order-2 sm:order-1">
          {{ showSuccessReport ? __('Close') : __('Cancel') }}
        </Button>

        <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3 order-1 sm:order-2">
          <!-- Validation Warning (only in entry mode) -->
          <div v-if="!canSubmit && closingData && !showSuccessReport"
            class="text-xs md:text-sm text-yellow-600 font-medium text-center sm:text-end">
            {{ validationMessage }}
          </div>

          <!-- Success message (shown in report view) -->
          <div v-if="showSuccessReport" class="text-xs md:text-sm text-green-600 font-medium text-center sm:text-end">
            {{ __('✓ Shift closed successfully') }}
          </div>

          <!-- Submit/Close button (only shown in entry mode) -->
          <Button v-if="!showSuccessReport" variant="solid" theme="blue" @click="submitClosing"
            :loading="isSubmitting" :disabled="!canSubmit">
            {{ isSubmitting ? __('Closing Shift...') : __('Close Shift') }}
          </Button>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Button, Dialog, Input } from "frappe-ui"
import { storeToRefs } from "pinia"
import { computed, reactive, ref, watch } from "vue"
import { call } from "@/utils/apiWrapper"
import { isOffline } from "@/utils/offline/sync"
import { renderReportPrintFormat } from "@/utils/reportPrintFormat"
import { useFormatters } from "../composables/useFormatters"
import { useShift } from "../composables/useShift"
import { usePOSSettingsStore } from "../stores/posSettings"
import TranslatedHTML from "./common/TranslatedHTML.vue"

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true,
  },
  openingShift: {
    type: String,
    required: true,
    validator: (value) => value && value.length > 0,
  },
})

const emit = defineEmits(["update:modelValue", "shift-closed"])

const open = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
})

const {
  getClosingShiftData,
  submitClosingShift,
  buildOfflineClosingData,
  submitClosingShiftOffline,
} = useShift()
const { formatCurrency, formatQuantity, formatDateTime, formatTime } = useFormatters()
const posSettingsStore = usePOSSettingsStore()
const { hideExpectedAmount } = storeToRefs(posSettingsStore)

const closingData = ref(null)
const closingDataResource = getClosingShiftData
const submitResource = submitClosingShift
const showInvoiceDetails = ref(false)
const showSuccessReport = ref(false) // Track if shift is closed and showing report
const errorMessage = ref('') // User-friendly error message

// Offline loading/submit state (the createResources aren't used offline)
const offlineLoading = ref(false)
const offlineSubmitting = ref(false)
const isLoadingData = computed(() => closingDataResource.loading || offlineLoading.value)
const isSubmitting = computed(() => submitResource.loading || offlineSubmitting.value)

// Watch dialog open state
watch(open, async (isOpen) => {
  if (isOpen && props.openingShift) {
    // Refresh POS settings to get latest hideExpectedAmount value
    await posSettingsStore.reloadSettings()
    loadClosingData()
  }
})

async function loadClosingData() {
  try {
    errorMessage.value = '' // Clear any previous errors

    let data
    if (isOffline()) {
      offlineLoading.value = true
      try {
        data = await buildOfflineClosingData(props.openingShift)
      } finally {
        offlineLoading.value = false
      }
    } else {
      data = await closingDataResource.submit({
        opening_shift: props.openingShift,
      })
    }

    // Make payment_reconciliation reactive
    if (data.payment_reconciliation) {
      data.payment_reconciliation = data.payment_reconciliation.map((payment) =>
        reactive({
          ...payment,
          closing_amount:
            payment.closing_amount ?? payment.expected_amount ?? 0,
          difference: 0,
        }),
      )

      // Calculate initial differences
      data.payment_reconciliation.forEach((payment) => {
        calculateDifference(payment)
      })
    }

    closingData.value = data

    // Auto-expand invoice details if there are few invoices
    if (invoiceCount.value > 0 && invoiceCount.value <= 10) {
      showInvoiceDetails.value = true
    }
  } catch (error) {
    console.error("Error loading closing data:", error)
    errorMessage.value = 'Unable to load shift data. Please check your connection and try again.'
  }
}

function calculateDifference(payment) {
  const closing = Number.parseFloat(payment.closing_amount) || 0
  const expected = Number.parseFloat(payment.expected_amount) || 0
  payment.difference = closing - expected
}

// New function to handle closing amount updates with proper reactivity
function updateClosingAmount(payment, value) {
  payment.closing_amount = value
  calculateDifference(payment)
}

function isBlankClosingAmount(payment) {
  return (
    payment.closing_amount === null ||
    payment.closing_amount === undefined ||
    payment.closing_amount === ""
  )
}

// Whether the shift expected any money through this payment method at all
// (opening balance or sales). When it expected nothing, 0 is the correct count.
function expectsMoney(payment) {
  return (Number.parseFloat(payment.expected_amount) || 0) > 0
}

// A counted amount is valid when it is filled in, not negative, and greater
// than zero wherever money was actually expected. A payment method with no
// opening balance and no movement expects 0, so counting 0 is right — requiring
// a positive number there made such shifts impossible to close, leaving the
// opening shift Open forever and blocking the next one. Mirrors
// POSClosingShift.validate_closing_amounts on the server.
function isValidClosingAmount(payment) {
  if (isBlankClosingAmount(payment)) return false
  const amount = Number.parseFloat(payment.closing_amount)
  if (!Number.isFinite(amount) || amount < 0) return false
  return expectsMoney(payment) ? amount > 0 : true
}

// Only a zero that is actually wrong — i.e. money was expected but none counted.
function isZeroClosingAmount(payment) {
  if (isBlankClosingAmount(payment)) return false
  return expectsMoney(payment) && Number.parseFloat(payment.closing_amount) === 0
}

// Payment methods whose counted amount is missing or inconsistent
const invalidPayments = computed(() => {
  if (!closingData.value || !closingData.value.payment_reconciliation) return []
  return closingData.value.payment_reconciliation.filter(
    (payment) => !isValidClosingAmount(payment),
  )
})

const zeroPayments = computed(() =>
  invalidPayments.value.filter((payment) => isZeroClosingAmount(payment)),
)

const validationMessage = computed(() => {
  if (!invalidPayments.value.length) return ''
  if (zeroPayments.value.length === invalidPayments.value.length) {
    return __('Actual amount cannot be 0 for: {0}', [
      zeroPayments.value.map((p) => p.mode_of_payment).join(', '),
    ])
  }
  return __('Please enter a valid counted amount for every payment method')
})

const canSubmit = computed(() => {
  if (!closingData.value || !closingData.value.payment_reconciliation)
    return false

  // Every payment method must have a counted amount that matches what the
  // shift expected (see isValidClosingAmount)
  return invalidPayments.value.length === 0
})

async function submitClosing() {
  if (!closingData.value) return

  // Block closing while any payment method is uncounted, negative, or zero
  // where money was expected
  if (invalidPayments.value.length) {
    errorMessage.value = __(
      'Please enter a valid counted amount for: {0}',
      [invalidPayments.value.map((p) => p.mode_of_payment).join(', ')],
    )
    return
  }

  try {
    errorMessage.value = '' // Clear any previous errors

    // Ensure all differences are calculated
    if (closingData.value.payment_reconciliation) {
      closingData.value.payment_reconciliation.forEach((payment) => {
        calculateDifference(payment)
      })
    }

    if (isOffline()) {
      // Offline: queue the closing and render the Z-report locally
      offlineSubmitting.value = true
      try {
        await submitClosingShiftOffline(closingData.value)
      } finally {
        offlineSubmitting.value = false
      }
      printClosingShiftLocal(closingData.value)
    } else {
      // Submit to server
      const result = await submitResource.submit({ closing_shift: closingData.value })

      // Print closing shift
      if (result && result.name) {
        printClosingShift(result.name)
      }

      // ...and the item-level summary for the same shift day. Not awaited: the
      // shift is closed either way, so the dialog should not sit open waiting
      // for a report to render.
      printItemSalesSummary(closingData.value)
    }

    // Shift is closed: dismiss the dialog right away, no success report
    emit("shift-closed")
    closeDialog()
  } catch (error) {
    console.error("Error submitting closing shift:", error)
    errorMessage.value = 'Failed to close shift. Please verify all amounts and try again.'
  }
}

function printClosingShift(name) {
  const params = new URLSearchParams({
    doctype: 'POS Closing Shift',
    name: name,
    format: 'POS Closing Shift',
    no_letterhead: 1,
    _lang: 'en',
    trigger_print: 1,
    _t: Date.now(),
  })
  window.open(`/printview?${params.toString()}`, '_blank', 'width=800,height=600')
}

/**
 * Show `html` in its own print window, the way /printview shows the Z-report.
 *
 * A report has no /printview URL of its own - that route prints a document, not
 * a report - so the rendered page is written into the window here and prints
 * itself on load. The cashier gets the same window and the same preview either
 * way, which is the point: one closing, two receipts that behave alike.
 */
function openPrintWindow(html) {
  const win = window.open("", "_blank", "width=800,height=600")
  if (!win) {
    console.error("Print window was blocked by the browser")
    return
  }

  // Escaped so the SFC parser does not read it as the end of this script block
  const autoPrint = "<script>window.onload=function(){window.print()}<\/script>"

  win.document.open()
  win.document.write(html.replace("</body>", `${autoPrint}</body>`))
  win.document.close()
}

// The report printed alongside the Z-report, and the Print Format it is printed
// with. Both are named the same thing; the format is the one linked to the
// report, so the receipt is identical to the one Reports prints.
const ITEM_SALES_SUMMARY_REPORT = "POS Item Sales Summary"
const ITEM_SALES_SUMMARY_FORMAT = "POS Item Sales Summary"

// The shift day the report groups by runs 09:00 -> 09:00, so a shift opened
// after midnight still belongs to the day before. Kept in step with the CASE
// that buckets the day in the report query (Report: POS Item Sales Summary).
const SHIFT_DAY_START_HOUR = 9

/**
 * The shift day `period_start_date` falls in, as YYYY-MM-DD.
 *
 * Read off the string rather than a Date so the day is the one the server
 * stamped, whatever timezone the browser is in. Returns null if unparseable.
 */
function shiftDayOf(periodStartDate) {
  const parts = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2})/.exec(String(periodStartDate || ""))
  if (!parts) return null

  const [year, month, day, hour] = parts.slice(1).map(Number)
  if (hour >= SHIFT_DAY_START_HOUR) return parts[0].slice(0, 10)

  // UTC arithmetic so subtracting the day cannot land on a DST boundary
  return new Date(Date.UTC(year, month - 1, day - 1)).toISOString().slice(0, 10)
}

/**
 * Print the shift day's item sales summary, right after the Z-report.
 *
 * Goes through the POS report endpoints so the branch scope and the permission
 * checks are the ones Reports already applies. The format is a client-side (JS)
 * template, so it is rendered here and not on the server.
 *
 * Never throws: by the time this runs the shift is closed, and a report that
 * fails to print must not read to the cashier as a closing that failed.
 */
async function printItemSalesSummary(data) {
  const shiftDate = shiftDayOf(data?.period_start_date)
  if (!shiftDate) {
    console.error(
      "Cannot print item sales summary: unreadable shift start",
      data?.period_start_date,
    )
    return
  }

  const posProfile = data?.pos_profile || null
  const filters = { shift_date: shiftDate }

  try {
    const [report, layout] = await Promise.all([
      call("ecs_posnext.api.reports.run_pos_report", {
        report_name: ITEM_SALES_SUMMARY_REPORT,
        filters: JSON.stringify(filters),
        pos_profile: posProfile,
      }),
      call("ecs_posnext.api.reports.get_print_template", {
        report_name: ITEM_SALES_SUMMARY_REPORT,
        print_layout: ITEM_SALES_SUMMARY_FORMAT,
        pos_profile: posProfile,
      }),
    ])

    if (!layout?.template) {
      console.error("Item sales summary print format is empty")
      return
    }

    openPrintWindow(
      renderReportPrintFormat({
        template: layout.template,
        letterhead: layout.letterhead,
        orientation: "Portrait",
        reportName: ITEM_SALES_SUMMARY_REPORT,
        title: __("POS Item Sales Summary"),
        columns: report?.columns || [],
        rows: report?.result || [],
        filters,
      }),
    )
  } catch (error) {
    console.error("Error printing item sales summary:", error)
  }
}

// Render a Z-report locally when closing offline (the server regenerates the
// official document on sync). Opens a printable window built from local totals.
function printClosingShiftLocal(data) {
  try {
    const rows = (data.payment_reconciliation || [])
      .map(
        (p) => `<tr>
          <td>${p.mode_of_payment}</td>
          <td class="num">${formatCurrency(p.opening_amount)}</td>
          <td class="num">${formatCurrency(p.expected_amount)}</td>
          <td class="num">${formatCurrency(p.closing_amount || 0)}</td>
          <td class="num">${formatCurrency((Number(p.closing_amount) || 0) - Number(p.expected_amount || 0))}</td>
        </tr>`,
      )
      .join("")

    const html = `<!doctype html><html><head><meta charset="utf-8">
      <title>${__("Shift Closing (Offline)")}</title>
      <style>
        body{font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#111;padding:16px;max-width:420px;margin:0 auto}
        h2{text-align:center;margin:0 0 4px}
        .muted{color:#666;text-align:center;margin:0 0 12px;font-size:11px}
        table{width:100%;border-collapse:collapse;margin:8px 0}
        th,td{border-bottom:1px solid #ddd;padding:5px 6px;text-align:left}
        th{background:#f3f4f6}
        .num{text-align:right;font-variant-numeric:tabular-nums}
        .tot{display:flex;justify-content:space-between;padding:4px 6px;font-weight:bold}
        .badge{display:inline-block;background:#fde68a;color:#92400e;border-radius:4px;padding:2px 8px;font-size:10px}
      </style></head><body>
      <h2>${__("Shift Closing (Z-Report)")}</h2>
      <p class="muted">
        <span class="badge">${__("OFFLINE — pending sync")}</span><br>
        ${data.pos_profile || ""}<br>
        ${data.period_start_date ? formatDateTime(data.period_start_date) : ""}
      </p>
      <div class="tot"><span>${__("Gross Sales")}</span><span>${formatCurrency(data.sales_total || data.grand_total || 0)}</span></div>
      <div class="tot"><span>${__("Net Sales")}</span><span>${formatCurrency(data.grand_total || 0)}</span></div>
      <div class="tot"><span>${__("Invoices")}</span><span>${data.sales_count || 0}</span></div>
      <table>
        <thead><tr>
          <th>${__("Method")}</th><th class="num">${__("Opening")}</th>
          <th class="num">${__("Expected")}</th><th class="num">${__("Actual")}</th>
          <th class="num">${__("Diff")}</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <p class="muted">${__("Official figures are confirmed when this shift syncs to the server.")}</p>
      <script>window.onload=function(){window.print()}<\/script>
      </body></html>`

    const win = window.open("", "_blank", "width=480,height=640")
    if (win) {
      win.document.open()
      win.document.write(html)
      win.document.close()
    }
  } catch (error) {
    console.error("Error rendering offline Z-report:", error)
  }
}

function closeDialog() {
  // Emit shift-closed event if we're closing from success report
  if (showSuccessReport.value) {
    emit("shift-closed")
  }

  open.value = false
  closingData.value = null
  showInvoiceDetails.value = false
  showSuccessReport.value = false // Reset report view
  errorMessage.value = '' // Clear error messages
}

// UI State Computed Properties
const shouldShowSummary = computed(() =>
  !hideExpectedAmount.value || showSuccessReport.value
)

const isInEntryMode = computed(() =>
  hideExpectedAmount.value && !showSuccessReport.value
)

const reconciliationMessage = computed(() => {
  if (isInEntryMode.value) {
    return 'Enter the actual counted amounts for each payment method'
  }
  if (showSuccessReport.value && hideExpectedAmount.value) {
    return 'Shift closed successfully - Review the final reconciliation below'
  }
  return 'Count your cash and enter actual amounts below'
})

// Computed properties for real-time recalculation
const invoiceCount = computed(() => {
  if (!closingData.value) return 0
  const transactions = closingData.value.pos_transactions || []
  return transactions.length
})

// Check if there are any return invoices
const hasReturns = computed(() => {
  if (!closingData.value) return false
  return (closingData.value.returns_count || 0) > 0
})

// Count of sales invoices (non-returns)
const salesInvoiceCount = computed(() => {
  if (!closingData.value) return 0
  const transactions = closingData.value.pos_transactions || []
  return transactions.filter(t => !t.is_return).length
})

const totalTax = computed(() => {
  if (!closingData.value || !closingData.value.taxes) return 0
  return closingData.value.taxes.reduce(
    (sum, tax) => sum + Number.parseFloat(tax.amount || 0),
    0,
  )
})

const grossSales = computed(() => {
  if (!closingData.value) return 0
  return closingData.value.sales_total ?? closingData.value.grand_total ?? 0
})
const getTotalExpected = computed(() => {
  if (!closingData.value || !closingData.value.payment_reconciliation) return 0
  return closingData.value.payment_reconciliation.reduce(
    (sum, payment) => sum + Number.parseFloat(payment.expected_amount || 0),
    0,
  )
})

const getTotalActual = computed(() => {
  if (!closingData.value || !closingData.value.payment_reconciliation) return 0
  return closingData.value.payment_reconciliation.reduce(
    (sum, payment) => sum + Number.parseFloat(payment.closing_amount || 0),
    0,
  )
})

const getTotalDifference = computed(() => {
  return getTotalActual.value - getTotalExpected.value
})

function getSalesForPayment(payment) {
  return (
    Number.parseFloat(payment.expected_amount || 0) -
    Number.parseFloat(payment.opening_amount || 0)
  )
}

function getShiftDuration() {
  if (!closingData.value || !closingData.value.period_start_date) return __("N/A")

  const start = new Date(closingData.value.period_start_date)
  const end = new Date()
  const diff = end - start

  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))

  if (hours > 0) {
    return __('{0}h {1}m', [hours, minutes])
  }
  return __('{0}m', [minutes])
}

function getPaymentIcon(method) {
  const methodLower = method.toLowerCase()

  if (methodLower.includes("cash")) {
    return { icon: "💵", color: "bg-green-500" }
  } else if (
    methodLower.includes("card") ||
    methodLower.includes("credit") ||
    methodLower.includes("debit")
  ) {
    return { icon: "💳", color: "bg-blue-500" }
  } else if (
    methodLower.includes("mobile") ||
    methodLower.includes("wallet") ||
    methodLower.includes("upi") ||
    methodLower.includes("phone")
  ) {
    return { icon: "📱", color: "bg-purple-500" }
  } else if (methodLower.includes("bank") || methodLower.includes("transfer")) {
    return { icon: "🏦", color: "bg-indigo-500" }
  } else if (methodLower.includes("cheque") || methodLower.includes("check")) {
    return { icon: "📝", color: "bg-yellow-500" }
  } else {
    return { icon: "💰", color: "bg-gray-500" }
  }
}
</script>
