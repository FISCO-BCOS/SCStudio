
pragma solidity ^0.4.6;

/**
 * A token that can increase its supply by another contract.
 *
 * This allows uncapped crowdsale by dynamically increasing the supply when money pours in.
 * Only mint agents, contracts whitelisted by owner, can mint new tokens.
 *
 */
contract MintableToken {

  uint256 public totalSupply;
  mapping(address => uint256) balances;
  
  event Transfer(address indexed from, address indexed to, uint256 value);

  /**
   * Create new tokens and allocate them to an address..
   *
   * Only callably by a crowdsale contract (mint agent).
   */
  function mint(address receiver, uint amount) public {
    totalSupply = totalSupply + amount;
    balances[receiver] = balances[receiver] + amount;
    Transfer(0, receiver, amount);
  }

  function transfer1(address _to, uint256 _value) returns (bool) {
    balances[msg.sender] = balances[msg.sender] - _value;
    balances[_to] = balances[_to] + _value;
    Transfer(msg.sender, _to, _value);
    return true;
  }

  function transfer2(address _to, uint256 _value) returns (bool) {
    balances[msg.sender] -= _value;
    balances[_to] += _value;
    Transfer(msg.sender, _to, _value);
    return true;
  }

}

