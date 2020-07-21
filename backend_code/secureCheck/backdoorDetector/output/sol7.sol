pragma solidity ^0.4.6;

contract Overflow {
  struct Account {
    address addr;
    uint balance;
  }
  
  Account[] accounts1;
  Account[] accounts2;
  Account[] accounts3;
  
  function applyInterest3_1 () public returns (uint) {
    for(uint i = 0; i < accounts1.length; i++) {
      accounts1[i].balance = accounts1[i].balance * 105 / 100;
    }
    return accounts1.length;
  }

  function applyInterest3_2 () public returns (uint) {
    for(uint i = 0; i < accounts2.length; i++) {
      accounts2[i].balance = accounts2[i].balance * 106 / 100;
    }
    return accounts2.length;
  }

  function applyInterest3_3 () public returns (uint) {
    for(uint i = 0; i < accounts3.length; i++) {
      accounts3[i].balance = accounts3[i].balance * 107 / 100;
    }
    return accounts3.length;
  }

  function interrupt () public returns (uint) {
    for(uint i = 0; i < accounts3.length; i++) {
      accounts3[i].balance = accounts3[i].balance * 108 / 100;
    }
    return accounts3.length;
  }

}