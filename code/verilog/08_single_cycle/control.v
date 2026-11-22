module control (
    input  wire [31:0] instr,
    input  wire [31:0] r1,
    input  wire [31:0] r2,

    output wire [31:0] imm,
    output wire        wreg,
    output wire [2:0]  wreg_src,
    output wire [1:0]  pc_src,
    output wire        branch_taken,
    output wire        alu_src_b,
    output wire [3:0]  alu_op,
    output wire        mem_write,
    output wire [2:0]  mem_func
);

    localparam ALU_ADD  = 4'd0;
    localparam ALU_SUB  = 4'd1;
    localparam ALU_AND  = 4'd2;
    localparam ALU_OR   = 4'd3;
    localparam ALU_XOR  = 4'd4;
    localparam ALU_SLT  = 4'd5;
    localparam ALU_SLTU = 4'd6;
    localparam ALU_SLL  = 4'd7;
    localparam ALU_SRL  = 4'd8;
    localparam ALU_SRA  = 4'd9;

    localparam [2:0] WR_IMM   = 3'd0;
    localparam [2:0] WR_PCIMM = 3'd1;
    localparam [2:0] WR_PC4   = 3'd2;
    localparam [2:0] WR_ALU   = 3'd3;
    localparam [2:0] WR_MEM   = 3'd4;

    localparam [1:0] PC_PC4  = 2'd0;
    localparam [1:0] PC_IMM  = 2'd1;
    localparam [1:0] PC_JALR = 2'd2;

    wire [6:0] opcode = instr[6:0];
    wire [2:0] funct3 = instr[14:12];
    wire [6:0] funct7 = instr[31:25];

    wire is_lui    = (opcode == 7'b0110111);
    wire is_auipc  = (opcode == 7'b0010111);
    wire is_jal    = (opcode == 7'b1101111);
    wire is_jalr   = (opcode == 7'b1100111);
    wire is_branch = (opcode == 7'b1100011);
    wire is_load   = (opcode == 7'b0000011);
    wire is_store  = (opcode == 7'b0100011);
    wire is_itype  = (opcode == 7'b0010011);
    wire is_rtype  = (opcode == 7'b0110011);

    wire [31:0] imm_i = {{20{instr[31]}}, instr[31:20]};
    wire [31:0] imm_s = {{20{instr[31]}}, instr[31:25], instr[11:7]};
    wire [31:0] imm_b = {{19{instr[31]}}, instr[31], instr[7], instr[30:25], instr[11:8], 1'b0};
    wire [31:0] imm_u = {instr[31:12], 12'b0};
    wire [31:0] imm_j = {{11{instr[31]}}, instr[31], instr[19:12], instr[20], instr[30:21], 1'b0};

    reg [31:0] imm_r;
    always @(*) begin
        case (opcode)
            7'b0110111, 7'b0010111: imm_r = imm_u;
            7'b1101111:              imm_r = imm_j;
            7'b1100111, 7'b0010011, 7'b0000011: imm_r = imm_i;
            7'b0100011:              imm_r = imm_s;
            7'b1100011:              imm_r = imm_b;
            default:                 imm_r = 32'b0;
        endcase
    end
    assign imm = imm_r;

    assign wreg = is_lui || is_auipc || is_jal || is_jalr || is_load || is_itype || is_rtype;

    reg [2:0] wreg_src_r;
    always @(*) begin
        if (is_lui)                    wreg_src_r = WR_IMM;
        else if (is_auipc)             wreg_src_r = WR_PCIMM;
        else if (is_jal || is_jalr)    wreg_src_r = WR_PC4;
        else if (is_load)              wreg_src_r = WR_MEM;
        else                           wreg_src_r = WR_ALU;
    end
    assign wreg_src = wreg_src_r;

    wire eq  = (r1 == r2);
    wire lt  = ($signed(r1) < $signed(r2));
    wire ltu = (r1 < r2);

    reg branch_taken_r;
    always @(*) begin
        case (funct3)
            3'b000: branch_taken_r = eq;
            3'b001: branch_taken_r = !eq;
            3'b100: branch_taken_r = lt;
            3'b101: branch_taken_r = !lt;
            3'b110: branch_taken_r = ltu;
            3'b111: branch_taken_r = !ltu;
            default: branch_taken_r = 1'b0;
        endcase
    end
    assign branch_taken = branch_taken_r;

    reg [1:0] pc_src_r;
    always @(*) begin
        if (is_jal || (is_branch && branch_taken_r)) pc_src_r = PC_IMM;
        else if (is_jalr)                            pc_src_r = PC_JALR;
        else                                         pc_src_r = PC_PC4;
    end
    assign pc_src = pc_src_r;

    assign alu_src_b = is_itype || is_load || is_store;

    reg [3:0] alu_op_r;
    always @(*) begin
        if (is_itype) begin
            case (funct3)
                3'b000: alu_op_r = ALU_ADD;
                3'b010: alu_op_r = ALU_SLT;
                3'b011: alu_op_r = ALU_SLTU;
                3'b100: alu_op_r = ALU_XOR;
                3'b110: alu_op_r = ALU_OR;
                3'b111: alu_op_r = ALU_AND;
                3'b001: alu_op_r = ALU_SLL;
                3'b101: alu_op_r = funct7[5] ? ALU_SRA : ALU_SRL;
                default: alu_op_r = ALU_ADD;
            endcase
        end else if (is_rtype) begin
            case (funct3)
                3'b000: alu_op_r = funct7[5] ? ALU_SUB : ALU_ADD;
                3'b001: alu_op_r = ALU_SLL;
                3'b010: alu_op_r = ALU_SLT;
                3'b011: alu_op_r = ALU_SLTU;
                3'b100: alu_op_r = ALU_XOR;
                3'b101: alu_op_r = funct7[5] ? ALU_SRA : ALU_SRL;
                3'b110: alu_op_r = ALU_OR;
                3'b111: alu_op_r = ALU_AND;
                default: alu_op_r = ALU_ADD;
            endcase
        end else begin
            alu_op_r = ALU_ADD;
        end
    end
    assign alu_op = alu_op_r;

    assign mem_write = is_store;
    assign mem_func  = funct3;

endmodule
