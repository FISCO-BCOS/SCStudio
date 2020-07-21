pragma solidity ^0.4.6;

contract NaiveBank {
  struct Account {
    address addr;
    uint balance;
  }
  
  Account[] accounts;
  
  function applyInterest1 () public returns (uint) {
    for(uint i = 0; i < accounts.length && msg.gas > 100000; i++) {
      accounts[i].balance = accounts[i].balance * 105 / 100;
    }
    return accounts.length;
  }
}