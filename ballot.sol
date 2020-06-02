pragma solidity >=0.4.22;

contract Ballot {
    struct Voter {
        bool voted;
        uint8 ticket;
        uint8 weight;
    }

    mapping(address => Voter) voters;
    mapping(address => bool) candidators;

    function isCandidate(address addr) public view returns (bool) {
        return candidators[addr];
    }

    function vote(address candidate) public returns (uint8) {
        uint8 _ticket = voters[msg.sender].ticket;
        uint8 _weight = voters[msg.sender].weight;
        
    }
}