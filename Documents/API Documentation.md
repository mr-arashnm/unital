# API Documentation

## {{base_url}}/auth/login/

---

## complexes app

### {{base_url}}/building

- list of all building with 
  
  - building name
  
  - building adress
  
  - building type

### {{base_url}}/building/{id}

- information about building with id = id
  
  - building name
  
  - building adress
  
  - building type
  
  - total floor
  
  - total unit
  
  - total parking
  
  - total warehouse

### {{base_url}}/building/{id}/unit

- list of all this building units
  
  - unit code
  
  - unit type
  
  - unit owner
  
  - unit resident

### {{base_url}}/building/{id}/unit/{id}

- information about unit with id = id and in building id = id
  
  - unit code
  
  - unit type
  
  - unit owner
  
  - unit resident
  
  - unit area
  
  - link to this unit parkings
  
  - link to this unit warehouses
  
  - link to unit ownership history
  
  - link to unit resident history 



### {{base_url}}/building/{id}/unit/{id}/TransferHistory

- list of all this unit TransferHistory
  
  - transfer_type
  
  - previous_owner
  
  - previous_resident
  
  - new_owner
  
  - new_resident
  
  - transfer_date
  
  - contract_number
  
  - contract_date



### {{base_url}}/building/{id}/unit/{id}/TransferHistory/{id}

- information about TransferHistory with id = id
  
  - transfer_type
  
  - previous_owner
  
  - previous_resident
  
  - new_owner
  
  - new_resident
  
  - transfer_date
  
  - contract_number
  
  - contract_date
  
  - description



### {{base_url}}/building/{id}/parking

- list of all this building parking
  
  - parking code
  
  - parking owner
  
  - parking resident

### {{base_url}}/building/{id}/parking/{id}

- information about parking with id = id and in building id = id
  
  - parking code
  
  - parking owner
  
  - parking resident
  
  - link to this parking owner
  
  - link to this parking resident
  
  - link to parking ownership history
  
  - link to parking resident history

### {{base_url}}/building/{id}/warehous

- list of all this building parking
  
  - warehous code
  
  - warehous owner
  
  - warehous resident

### {{base_url}}/building/{id}/warehous/{id}

- information about parking with id = id and in building id = id
  
  - warehous code
  
  - warehous area
  
  - warehous owner
  
  - warehous resident
  
  - link to this warehous owner
  
  - link to this warehous resident
  
  - link to warehous ownership history
  
  - link to warehous resident history
