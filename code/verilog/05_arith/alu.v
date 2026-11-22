module alu (
    input  wire [31:0] a,
    input  wire [31:0] b,
    input  wire [3:0]  alu_op,
    output reg  [31:0] result,
    output wire        zero
);

    localparam ALU_ADD = 4'd0;
    localparam ALU_SUB = 4'd1;
    localparam ALU_AND = 4'd2;
    localparam ALU_OR  = 4'd3;
    localparam ALU_XOR = 4'd4;
    localparam ALU_SLT = 4'd5;
    localparam ALU_SLL = 4'd6;
    localparam ALU_SRL = 4'd7;

    wire [31:0] b_operand;
    wire        carry_in;
    wire [31:0] add_result;
    wire        add_cout;

    assign b_operand = (alu_op == ALU_SUB) ? ~b : b;
    assign carry_in  = (alu_op == ALU_SUB) ? 1'b1 : 1'b0;

    adder_32 u_adder (
        .a    (a),
        .b    (b_operand),
        .cin  (carry_in),
        .sum  (add_result),
        .cout (add_cout)
    );

    always @(*) begin
        case (alu_op)
            ALU_ADD: result = add_result;
            ALU_SUB: result = add_result;
            ALU_AND: result = a & b;
            ALU_OR:  result = a | b;
            ALU_XOR: result = a ^ b;
            ALU_SLT: result = (a[31] != b[31]) ? {31'b0, a[31]} : {31'b0, (a < b)};
            ALU_SLL: result = a << b[4:0];
            ALU_SRL: result = a >> b[4:0];
            default: result = 32'b0;
        endcase
    end

    assign zero = (result == 32'b0);

endmodule
