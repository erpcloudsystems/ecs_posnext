<template>
  <v-container fluid class="container1">
    <!-- Header -->
    <v-card flat class="cards mb-2 mt-2 py-2">
      <v-row align="center" no-gutters>
        <v-col cols="1">
          <v-btn block class="pa-1" color="warning" dark @click="goBack">
            {{ __("Back") }}
          </v-btn>
        </v-col>
        <v-col cols="2" class="text-center">
          <h2>{{ hourlyView ? 'معدل بالساعة' : 'معدل التشغيل' }}</h2>
        </v-col>
        <v-col cols="1">
          <v-checkbox v-model="hourlyView" label="بالساعة" dense hide-details class="mt-0"></v-checkbox>
        </v-col>
        <v-col cols="2">
          <v-menu v-model="menuFromDate" :close-on-content-click="false" transition="scale-transition" offset-y min-width="auto">
            <template v-slot:activator="{ on, attrs }">
              <v-text-field v-model="filters.from_date" label="من تاريخ" prepend-icon="mdi-calendar" readonly v-bind="attrs" v-on="on" dense outlined hide-details></v-text-field>
            </template>
            <v-date-picker v-model="filters.from_date" @input="menuFromDate = false"></v-date-picker>
          </v-menu>
        </v-col>
        <v-col cols="2">
          <v-menu v-model="menuToDate" :close-on-content-click="false" transition="scale-transition" offset-y min-width="auto">
            <template v-slot:activator="{ on, attrs }">
              <v-text-field v-model="filters.to_date" label="إلى تاريخ" prepend-icon="mdi-calendar" readonly v-bind="attrs" v-on="on" dense outlined hide-details></v-text-field>
            </template>
            <v-date-picker v-model="filters.to_date" @input="menuToDate = false"></v-date-picker>
          </v-menu>
        </v-col>
        <v-col cols="1" v-if="!hourlyView">
          <v-select v-model="filters.day_of_week" :items="daysOfWeek" item-text="label" item-value="value" label="اليوم" dense outlined hide-details clearable></v-select>
        </v-col>
        <v-col cols="2">
          <v-select v-model="filters.warehouse" :items="warehouses" :label="__('Warehouse')" dense outlined hide-details clearable></v-select>
        </v-col>
        <v-col cols="2">
          <v-select v-model="filters.item_group" :items="itemGroups" :label="__('Item Group')" dense outlined hide-details clearable></v-select>
        </v-col>
        <v-col cols="2" class="text-right">
          <v-btn color="primary" @click="fetchReport" :loading="loading" class="mr-2">
            <v-icon left>mdi-magnify</v-icon>
            {{ __("Search") }}
          </v-btn>
          <v-btn color="success" @click="exportToExcel" :disabled="!items.length">
            <v-icon left>mdi-file-excel</v-icon>
          </v-btn>
        </v-col>
      </v-row>
    </v-card>

    <!-- Summary -->
    <v-card flat class="cards mb-2 pa-2" v-if="summary.total_items">
      <v-row>
        <v-col cols="3">
          <v-chip color="primary" dark>
            <v-icon left small>mdi-calendar-range</v-icon>
            {{ summary.date_from }} → {{ summary.date_to }}
          </v-chip>
        </v-col>
        <v-col cols="2" v-if="summary.num_days">
          <v-chip color="info" dark>
            {{ summary.num_days }} يوم
          </v-chip>
        </v-col>
        <v-col cols="2">
          <v-chip color="success" dark>
            {{ summary.total_items }} صنف
          </v-chip>
        </v-col>
      </v-row>
    </v-card>

    <!-- Data Table -->
    <v-card class="pa-2" style="max-height: 75vh; overflow-y: auto;">
      <v-text-field v-model="search" append-icon="mdi-magnify" :label="__('Search')" single-line hide-details dense outlined class="mb-2"></v-text-field>
      
      <v-data-table
        :headers="headers"
        :items="items"
        :search="search"
        :loading="loading"
        item-key="item_code"
        dense
        :items-per-page="50"
        class="elevation-0"
        fixed-header
        height="60vh"
      >
        <!-- Custom item slot for both views -->
        <template v-slot:item="{ item }">
          <tr v-if="hourlyView">
            <td>{{ item.item_name }}</td>
            <td class="text-center">{{ item.stock_uom }}</td>
            <td v-for="h in hours" :key="h" class="text-end">{{ formatNumber(item['hour_' + h]) }}</td>
            <td class="text-end"><v-chip small color="primary" dark>{{ formatNumber(item.total_qty) }}</v-chip></td>
          </tr>
          <tr v-else>
            <td>{{ item.item_name }}</td>
            <td class="text-center">{{ item.stock_uom }}</td>
            <td class="text-end">{{ formatNumber(item.week1) }}</td>
            <td class="text-end">{{ formatNumber(item.week2) }}</td>
            <td class="text-end">{{ formatNumber(item.week3) }}</td>
            <td class="text-end">{{ formatNumber(item.week4) }}</td>
            <td class="text-center"><v-chip small color="orange" dark>{{ formatNumber(item.daily_avg) }}</v-chip></td>
            <td class="text-center">{{ item.increase_rate }}</td>
            <td class="text-end"><v-chip small color="blue" dark>{{ formatNumber(item.total_required) }}</v-chip></td>
            <td class="text-end"><v-chip small :color="item.current_stock > 0 ? 'green' : 'grey'" dark>{{ formatNumber(item.current_stock) }}</v-chip></td>
            <td class="text-end"><v-chip small :color="item.required_qty > 0 ? 'red' : 'green'" dark>{{ formatNumber(item.required_qty) }}</v-chip></td>
          </tr>
        </template>
      </v-data-table>
    </v-card>
  </v-container>
</template>

<script>
export default {
  data() {
    return {
      loading: false,
      search: "",
      hourlyView: false,
      menuFromDate: false,
      menuToDate: false,
      filters: {
        warehouse: null,
        item_group: null,
        day_of_week: null,
        from_date: frappe.datetime.get_today(),
        to_date: frappe.datetime.get_today(),
      },
      daysOfWeek: [
        { value: 0, label: "السبت" },
        { value: 1, label: "الأحد" },
        { value: 2, label: "الإثنين" },
        { value: 3, label: "الثلاثاء" },
        { value: 4, label: "الأربعاء" },
        { value: 5, label: "الخميس" },
        { value: 6, label: "الجمعة" },
      ],
      warehouses: [],
      itemGroups: [],
      items: [],
      weeks: [],
      hours: [13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6],
      summary: {},
    };
  },

  computed: {
    headers() {
      if (this.hourlyView) {
        // Hourly view headers
        const baseHeaders = [
          { text: "الصنف", value: "item_name", align: "start", width: "200px" },
          { text: "الوحدة", value: "stock_uom", align: "center", width: "60px" },
        ];
        // Add hour columns (13:00 to 06:00)
        const hourHeaders = this.hours.map(h => ({
          text: `${h}:00`,
          value: `hour_${h}`,
          align: "end",
          width: "55px",
        }));
        baseHeaders.push(...hourHeaders);
        baseHeaders.push({ text: "الإجمالي", value: "total_qty", align: "end", width: "80px" });
        return baseHeaders;
      } else {
        // Weekly view headers
        return [
          { text: "الصنف", value: "item_name", align: "start", width: "200px" },
          { text: "الوحدة", value: "stock_uom", align: "center", width: "60px" },
          { text: "أسبوع 1", value: "week1", align: "end", width: "80px" },
          { text: "أسبوع 2", value: "week2", align: "end", width: "80px" },
          { text: "أسبوع 3", value: "week3", align: "end", width: "80px" },
          { text: "أسبوع 4", value: "week4", align: "end", width: "80px" },
          { text: "معدل يوم", value: "daily_avg", align: "center", width: "80px" },
          { text: "نسبة الزيادة", value: "increase_rate", align: "center", width: "80px" },
          { text: "اجمالي المطلوب", value: "total_required", align: "end", width: "100px" },
          { text: "جرد اليوم", value: "current_stock", align: "end", width: "90px" },
          { text: "المطلوب", value: "required_qty", align: "end", width: "90px" },
        ];
      }
    },
  },

  mounted() {
    this.loadFilters();
  },

  methods: {
    __(text) {
      return __(text);
    },

    goBack() {
      window.history.back();
    },

    formatNumber(num) {
      if (!num) return "0";
      return parseFloat(num).toLocaleString("en-US", { maximumFractionDigits: 2 });
    },

    async loadFilters() {
      try {
        const [warehousesRes, itemGroupsRes] = await Promise.all([
          frappe.call({ method: "posawesome.posawesome.api.operating_rate.get_warehouses" }),
          frappe.call({ method: "posawesome.posawesome.api.operating_rate.get_item_groups" }),
        ]);
        this.warehouses = warehousesRes.message || [];
        this.itemGroups = itemGroupsRes.message || [];
      } catch (e) {
        console.error("Failed to load filters:", e);
      }
    },

    async fetchReport() {
      this.loading = true;
      try {
        if (this.hourlyView) {
          // Hourly view
          const res = await frappe.call({
            method: "posawesome.posawesome.api.operating_rate.get_hourly_consumption_report",
            args: {
              warehouse: this.filters.warehouse,
              item_group: this.filters.item_group,
              from_date: this.filters.from_date,
              to_date: this.filters.to_date,
            },
          });
          
          if (res.message) {
            this.hours = res.message.hours || [];
            // Transform items to flatten hourly data for table
            this.items = (res.message.items || []).map(item => {
              const row = { ...item };
              // Add hour columns as flat properties
              this.hours.forEach(h => {
                row[`hour_${h}`] = item.hourly[String(h)] || 0;
              });
              return row;
            });
            this.summary = res.message.summary || {};
          }
        } else {
          // Weekly view
          const res = await frappe.call({
            method: "posawesome.posawesome.api.operating_rate.get_operating_rate_report",
            args: {
              warehouse: this.filters.warehouse,
              item_group: this.filters.item_group,
              day_of_week: this.filters.day_of_week,
              from_date: this.filters.from_date,
              to_date: this.filters.to_date,
            },
          });
          
          if (res.message) {
            this.items = res.message.items || [];
            this.weeks = res.message.weeks || [];
            this.summary = res.message.summary || {};
          }
        }
      } catch (e) {
        console.error("Failed to fetch report:", e);
        frappe.msgprint(__("Failed to load report"));
      }
      this.loading = false;
    },

    exportToExcel() {
      let exportData;
      if (this.hourlyView) {
        exportData = this.items.map(item => {
          const row = {
            "الصنف": item.item_name,
            "الوحدة": item.stock_uom,
          };
          this.hours.forEach(h => {
            row[`${h}:00`] = item[`hour_${h}`] || 0;
          });
          row["الإجمالي"] = item.total_qty;
          return row;
        });
      } else {
        exportData = this.items.map(item => ({
          "الصنف": item.item_name,
          "الوحدة": item.stock_uom,
          "أسبوع 1": item.week1,
          "أسبوع 2": item.week2,
          "أسبوع 3": item.week3,
          "أسبوع 4": item.week4,
          "معدل يوم": item.daily_avg,
          "نسبة الزيادة": item.increase_rate,
          "اجمالي المطلوب": item.total_required,
          "جرد اليوم": item.current_stock,
          "المطلوب": item.required_qty,
        }));
      }

      const headers = Object.keys(exportData[0] || {});
      const csv = [
        headers.join(","),
        ...exportData.map(row => headers.map(h => row[h]).join(","))
      ].join("\n");

      const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8;" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `معدل_التشغيل_${this.summary.date_from}_${this.summary.date_to}.xlsx`;
      link.click();
    },
  },
};
</script>

<style scoped>
.container1 {
  padding: 10px;
}
</style>
