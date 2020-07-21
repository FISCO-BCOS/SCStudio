pragma solidity ^0.4.6;

contract Overflow {
  struct Account {
    address addr;
    uint balance;
  }
  
  Account[] accounts;
  
  function applyInterest3 () public returns (uint) {
    for(var i = 0; i < accounts.length; i++) {
      accounts[i].balance = accounts[i].balance * 105 / 100;
    }
    return accounts.length;
  }
}