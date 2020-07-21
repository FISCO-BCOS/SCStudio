pragma solidity ^0.4.6;

contract DangerSend {
  struct Account {
    address addr;
    uint balance;
  }
  
  Account[] accounts;
  
  function applyInterest2 (uint amount) public {
    for(uint i = 0; i < accounts.length; i++) {
      accounts[i].addr.transfer(amount);
    }
  }
}