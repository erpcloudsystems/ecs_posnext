<template>
    <v-container fluid>
      <div class="row columns  ">
  
                  <v-card-title>{{__("Packing")}}</v-card-title>

        </div>
      <v-dialog
        v-model="itemDetails"
        max-width="1200px"
        class="overflow-y-none grey lighten-5"
        
      >
      <v-card
      
      class="cards my-0 p-0 grey lighten-5"
      v-if="itemDetails"
      >
      <v-data-table
        :headers="selected_items_header"
        :items="selected_items"
        :loading="item_loading"
        item-key="name"
        class="elevation-1 mt-0"
      >
      </v-data-table>
      </v-card>
    </v-dialog>
      <div class="kanban-board">
        <div class="row columns  "style="margin: 0;">
          <v-card
            v-for="task in columns.tasks"
            :key="task.id"
            outlined
            class=" "
          >
            <!-- Timer component that accepts inputTime -->
            <v-card-title @click="handleClickSalesOrder(task.name)">
              {{ task.name }}
            </v-card-title>
            <p  style="text-align: center; ">{{ task.custom_so_type }}</p>
            <v-divider></v-divider>
            <div  style="display: flex; justify-content: space-between; margin: 1rem; align-items: center;">
              <Timer :inputTime="task.time || 1800"  :id="task.name"/>
                <button @click="onClickHandle(task.name)">{{__("Done")}}</button>
            </div>
            <!-- <div style="text-align: left;">{{ task.custom_so_type }}</div> -->
            <v-divider v-if="task.posa_notes"></v-divider>
            {{ task.posa_notes }}
            <v-divider></v-divider>
            <div>
              <ul>
                <li
                  v-for="item in task.items"
                  :key="item"
                >
                  {{ item }}
                </li>
              </ul>
            </div>
          </v-card>

        </div>
      </div>
    </v-container>
  </template>
  
  <script>
  import Timer from '../../Timer.vue';
  import draggable from "vuedraggable";
  export default {
    components: {
      draggable,
      Timer
    },
    data() {
      return {
        columns: [
     
        ],
        itemDetails:false,
        selected_items_header: [
          {
            text: __("Item"),
            align: "start",
            sortable: true,
            value: "item_code",
          },
          {
            text: __("QTY"),
            align: "start",
            sortable: true,
            value: "qty",
          },
        ],
        selected_items:[],
        item_loading:false
      };
    },
    methods: {
      handleClickSalesOrder(sales_order) {
        this.itemDetails = true
        this.item_loading = true
        frappe.call({
            method: 'posawesome.posawesome.api.kitchen_order.get_items_sales_order',
            args: {
                name: sales_order,
            },
            callback: (r) => {
              if (!r.exc) {
                this.selected_items = r.message
                this.item_loading = false
              }
            },
          });
        console.log(sales_order)
      },
      getColumnClass(columnName) {
        switch (columnName) {
          case "Preparing":
            return "preparing-column";
          default:
            return "";
        }
      },

      onClickHandle(so) {
          frappe.call({
            method: 'posawesome.posawesome.api.kitchen_order.update_sales_order',
            args: {
                name: so,
                status:'Packing'
            },
            callback: (r) => {
                this.columns.tasks =  this.columns.tasks.filter(function(item) {
                    return item.name !== so
                })
               
              
            },
          });
        
       
        // console.log("Drag changed",   event);
        // console.log("column",   column);
        // Optional: Save changes to a database or server
        
      },
      cloneTask(task) {
        return { ...task };
      },
      handleRealtimeUpdate(data) {
        console.log(data)
        // Check if the new order should be added to the corresponding column
        // const column = this.columns.find(col => col.name === data.status_name);
        const existingTask = this.columns.tasks.find(task => task.id == data.order_id);

        if (!existingTask) {
          // Add the new task to the correct column
          this.columns.tasks.push({
            id: data.order_id,
            name: data.order_id,
            status_name: data.status_name,
            timer: data.status_name,
            custom_so_type: data.custom_so_type,
            items: data.items,
            branch: data.branch,
            posa_notes: data.posa_notes,
          });
        }
      },
      get_sales_order(){
        frappe.call({
          method: 'posawesome.posawesome.api.kitchen_order.get_sales_order',
          args:{
            status:"Packing",
          },
          callback: (r) => {
            if (!r.exc) {
              if (r.message.length > 0){
                
                this.columns = r.message[0]
              }
              console.log(r.message)
            }
          },
        });
      } 
    },
    mounted: function ()  {
      // Fetch data when the component is mounted
      this.get_sales_order();
      frappe.realtime.on('order_packing', this.handleRealtimeUpdate);
    },
    beforeDestroy() {
      // Cleanup the realtime listener
      frappe.realtime.off('order_packing', this.handleRealtimeUpdate);
    },
  };
  </script>
  
  <style scoped>
  .kanban-board {
    display: flex;
  }
  .columns {
    display: flex;
    gap: 20px;
  }
  .column {
    width: 250px;
  }
  .column-card {
    padding: 10px;
    background-color: #f4f4f4;
  }
  .task-list {
    min-height: 50px;
  }
  .task-card {
    margin-top: 10px;
    background-color: #ffffff;
  }
  /* Column color styles */
  .order-received-column {
    background-color: #fc7e08; /* Light orange */
    color: white;
  }
  
  .preparing-column {
    background-color: #5bc0de; /* Light blue */
    color: white;
  }
  
  .dining-column {
    background-color: #d9534f; /* Light red */
    color: white;
  }
  
  .packing-column {
    background-color: #f7b731; /* Light yellow */
    color: white;
  }
  
  .ready-to-pick-up-column {
    background-color: #0275d8; /* Light blue */
    color: white;
  }
  
  .completed-column {
    background-color: #5cb85c; 
    color: white;
  }
  </style>
  